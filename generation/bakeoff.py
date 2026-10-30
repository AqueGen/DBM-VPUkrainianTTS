#!/usr/bin/env python3
"""Render a handful of phrases through several TTS engines / settings so they can be
compared by ear in review.html.

Every run writes into generation/variants/<variant id>/<key>.ogg and records what was
actually sent to the engine in generation/variants/manifest.json. Variants are never
overwritten: a new setting means a new id, which shows up as a new column in the page.

Run:  python generation/bakeoff.py            # render every variant defined below
      python generation/bakeoff.py v3-caps    # render only these variants
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
VARIANTS_DIR = os.path.join(HERE, "variants")
MANIFEST = os.path.join(VARIANTS_DIR, "manifest.json")

import envvars

ELEVEN_KEY = envvars.get("ELEVENLABS_API_KEY", required=False)
AZURE_KEY = envvars.get("AZURE_SPEECH_KEY", required=False)
AZURE_REGION = envvars.get("AZURE_SPEECH_REGION", required=False)
MATILDA = "XrExE9yKIg1WjnnlVkGX"

# Round 1 - which engine. Failure modes behind the flagged phrases: single word, wrong
# stress, Russian-sounding vowels, slang, abbreviation, long line with punctuation.
ENGINE_KEYS = [
    "uu", "thanks", "defensive", "kite", "aesoon",
    "bait", "harmonic", "crowdcontrol", "interruptbyeye", "Thogar/B2D3",
]

# Round 2 - which wording. Every line that leans on WoW jargon, rendered twice on the
# same engine so the wording is the only thing that differs.
JARGON_KEYS = [
    "aesoon", "kite", "dotyou", "incomingdebuff", "throweyedebuff", "throweyehealer",
    "movemelee", "stackhigh", "killmob", "mobkill", "mobout", "mobsoon", "mobenough",
    "behindmob", "bringlighttomob", "movetomobs", "runovermobs",
]

# The same lines without the borrowed words. Longer, but understandable to someone who
# does not play - which is exactly what is being judged by ear.
PLAIN_WORDING = {
    "aesoon": "Скоро шкода по площі",
    "kite": "Відбігай",
    "dotyou": "Періодична шкода на тобі",
    "incomingdebuff": "Скоро негативний ефект",
    "throweyedebuff": "Кинь око гравцю з негативним ефектом",
    "throweyehealer": "Кинь око лікарю",
    "movemelee": "Іди в ближній бій",
    "stackhigh": "Багато накладень",
    "killmob": "Вбивай прислужників",
    "mobkill": "Вбивай прислужників",
    "mobout": "Витягни прислужників",
    "mobsoon": "Скоро прислужники",
    "mobenough": "Енергія повна, тримайся далі від прислужників",
    "behindmob": "За ворогом",
    "bringlighttomob": "Неси світло до ворога",
    "movetomobs": "Іди до ворогів",
    "runovermobs": "Пробіжи по ворогах",
}

# Stress written as a capital letter on the stressed vowel - the one hint the engine was
# thought to honour (a combining acute breaks it, see CLAUDE.md). Lost every row of
# round 1, kept here so the comparison stays on the page.
CAPS_STRESS = {
    "uu": "ТвоЄ",
    "thanks": "ДЯкую",
    "defensive": "ЗАхист",
    "kite": "КАйть",
    "aesoon": "СкОро АОЕ",
    "bait": "ПриманЮй зАраз",
    "harmonic": "ГармОнія",
    "crowdcontrol": "КонтролЮй",
    "interruptbyeye": "Збий заклЯття Оком.",
    "Thogar/B2D3": "КОлія два: підкрІплення, кОлія три: вОїни",
}

TURBO = {"engine": "elevenlabs", "model": "eleven_turbo_v2_5", "language_code": "uk"}
V3 = {"engine": "elevenlabs", "model": "eleven_v3"}

VARIANTS = [
    dict(TURBO, id="turbo-uk", label="ElevenLabs turbo v2.5, forced uk", keys=ENGINE_KEYS),
    dict(V3, id="v3", label="ElevenLabs v3, plain text", keys=ENGINE_KEYS),
    dict(V3, id="v3-caps", label="ElevenLabs v3, stress as a capital letter",
         keys=ENGINE_KEYS, override=CAPS_STRESS),
    {
        "id": "edge-polina",
        "label": "edge-tts uk-UA-PolinaNeural (free)",
        "engine": "edge",
        "voice": "uk-UA-PolinaNeural",
        "keys": ENGINE_KEYS,
    },
    # The whole pack in the voice that won by ear, so the verdict rests on 453 phrases
    # rather than ten. Same voice as Azure's uk-UA-PolinaNeural.
    {
        "id": "polina-all",
        "label": "Polina - whole pack",
        "engine": "edge",
        "voice": "uk-UA-PolinaNeural",
        "keys": "all",
    },
    dict(TURBO, id="jargon", label="wording: as shipped (jargon)", keys=JARGON_KEYS),
    dict(TURBO, id="plain-words", label="wording: no borrowed words",
         keys=JARGON_KEYS, override=PLAIN_WORDING),
]

# Round 3 - the voice itself. Matilda is an American-accent source voice, and ElevenLabs
# states that a voice's own accent leaks into multilingual output, so a Ukrainian-native
# voice may fix at the root what respelling and stress hints fight downstream.
# Ids from GET /v1/shared-voices?language=uk, picked for a bright, lively delivery.
# Rendered on v3, the expressive model: the goal of this round is a more human voice.
UKRAINIAN_VOICES = {}
# The 14 female and 4 male uk library voices with the most use, on eleven_v4. el2-* (v2) is
# only for a voice whose v4 clips run too long.
LIBRARY_VOICES = {
    "yaroslava": "0ZQZuw8Sn4cU0rN1Tm2K", "vira": "nCqaTnIbLdME87OuQaZY",
    "mariya": "2OXYbN1uGomXXJtv9Dq6", "solomiya": "yMBZR4SLoc24wOJLWAB2",
    "anna": "2o2uQnlGaNuV3ObRpxXt", "katerina-boyko": "Xx7Usst6zGAQKLjgeyV7",
    "ana": "5erHrdsmUNM63rFLhYiV", "alena": "BEprpS2vpgM32yNJpTXq",
    "sofiia": "96XEXOjZRHooATdYA8FY", "tonya": "bg0e02brzo3RVUEbuZeo",
    "kateryna": "X1WtgMmQUBwtiAPn4j1P", "kira": "2HWb7sZSrZqPB8HOI0KI",
    "marlena": "W4ZBKBsXCMS1XKvLLTlU", "alisa": "KBxO1LTAD4PE7D9rqUeb",
    "m-evgeniy": "Ntd0iVwICtUtA6Fvx27M", "m-alex": "9Sj8ugvpK1DmcAXyvi3a",
    "m-bogdan": "jn6ifzU1eO5tfUZ2ZJVg", "m-artem": "h9NSQvWZaC4NFusYsxT9",
}
for _name, _voice in LIBRARY_VOICES.items():
    for _tag, _model in (("el4", "eleven_v4"), ("el2", "eleven_multilingual_v2")):
        VARIANTS.append({"id": "%s-%s" % (_tag, _name), "label": "ElevenLabs %s: %s" % (_model, _name),
                         "engine": "elevenlabs", "model": _model, "voice": _voice, "keys": ENGINE_KEYS})
# What eleven_v4 hears instead, for the whole-pack renders only; v4 reads IPA between slashes.
# m-alex stressed "на" in "на тобі" like "here, take it": 5 of 5 test lines as text, 0 of 5 as IPA.
# The rest are words m-alex stressed off the norm (en.wiktionary uk-IPA). IPA as a whole line
# broke "Дев'ять", "Трощитель", "Провал" and "Спис", turned "воїни" into "воїні" and did not fix
# "Продовжуй", so those stay plain text.
ELEVEN_SPOKEN = {
    "на тобі": "/na toˈbʲi/",
    "колія": "/ˈkɔlija/", "колії": "/ˈkɔliji/", "кристал": "/krɪsˈtɑl/",
    # the owner wants the English acronym; "де-пе-ес" is the Azure spelling and m-alex spells it out
    "де-пе-ес": "DPS",
}
# Words m-alex got wrong in one line only and right everywhere else.
# "Спис" came out as "списка" on four takes, "Спис!" did not. "Вперед" came out as "вперьод"
# in 11 of 12 plain takes; the shipped com_go is the "Впе-ред" take with seed 3, picked by
# phones out of 9 (scratch takes.py), so a re-render of this text may not match it.
ELEVEN_OVERRIDE = {"fearsoon": "/ˈskɔrɔ/ страх", "left": "/liˈʋɔrut͡ʃ/",
                   "spear": "Спис!", "com_go": "Впе-ред, впе-ред, впе-ред!"}
# Picked voices, rendered over the whole pack before the budget goes to the next one.
# Shortlist in pick order: m-alex, m-evgeniy, solomiya.
for _name in ("m-alex", "m-evgeniy", "solomiya"):
    VARIANTS.append({"id": "el4-%s-all" % _name, "label": "ElevenLabs eleven_v4: %s - whole pack" % _name,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES[_name],
                     "keys": "all", "spoken": ELEVEN_SPOKEN,
                     # the overrides were found on m-alex; other voices go through the judge loop instead
                     "override": ELEVEN_OVERRIDE if _name == "m-alex" else {}})
# m-alex leans on "на" in "... на тобі" as if it were a verb ("here, take it"). Same two
# lines in other written forms; "same" re-renders the original text to show plain variance.
NA_FORMS = {
    "same": ("Стріла на тобі", "Поглинання на тобі"),
    "comma": ("Стріла, на тобі", "Поглинання, на тобі"),
    "dash": ("Стріла - на тобі", "Поглинання - на тобі"),
    "order": ("На тобі стріла", "На тобі поглинання"),
    "joined": ("Стріла натобі", "Поглинання натобі"),
}
for _form, (_arrow, _absorb) in NA_FORMS.items():
    VARIANTS.append({"id": "el4-m-alex-na-%s" % _form, "label": "m-alex, \"на тобі\": %s" % _form,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": ["arrowyou", "absorbyou"],
                     "override": {"arrowyou": _arrow, "absorbyou": _absorb}})
# None of those forms helped. The five worst "на тобі" lines: other voices as written, and
# m-alex with "в тебе" instead.
NA_KEYS = ["lineyou", "coinyou", "greenyou", "arrowyou", "absorbyou"]
for _name in ("m-evgeniy", "solomiya", "m-artem"):
    VARIANTS.append({"id": "el4-%s-na" % _name, "label": "%s, \"на тобі\"" % _name,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES[_name],
                     "keys": NA_KEYS})
for _form, _texts in (
        ("vtebe", ("Лінія в тебе", "Монета в тебе", "Зелений у тебе", "Стріла в тебе", "Поглинання в тебе")),
        ("utebe-first", ("У тебе лінія", "У тебе монета", "У тебе зелений", "У тебе стріла", "У тебе поглинання"))):
    VARIANTS.append({"id": "el4-m-alex-na-%s" % _form, "label": "m-alex, \"на тобі\": %s" % _form,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": NA_KEYS, "override": dict(zip(NA_KEYS, _texts))})
# The written line stays; only what the engine hears or how it samples changes. Levers from
# the v4 prompting docs: capitals add emphasis, IPA in slashes, audio tags; plus the API's
# stability and seed.
_NA_BASE = {"lineyou": "Лінія", "coinyou": "Монета", "greenyou": "Зелений", "arrowyou": "Стріла",
            "absorbyou": "Поглинання"}
for _form, _tail, _extra in (
        ("caps", "на ТОБІ", None),
        ("ipa", "/na toˈbʲi/", None),
        ("tag", "на тобі", None),
        ("stable", "на тобі", {"voice_settings": {"stability": 0.9, "similarity_boost": 0.75}}),
        ("seed1", "на тобі", {"seed": 1}),
        ("seed2", "на тобі", {"seed": 2})):
    _texts = {k: ("[calm] " if _form == "tag" else "") + "%s %s" % (w, _tail) for k, w in _NA_BASE.items()}
    VARIANTS.append({"id": "el4-m-alex-na-%s" % _form, "label": "m-alex, \"на тобі\": %s" % _form,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": NA_KEYS, "override": _texts, "extra": _extra})
# "де-пе-ес" is the Azure workaround; on m-alex it is read letter by letter. Other spellings,
# and takes of "Спис", which m-alex reads as "списка".
_DPS = {"dpshard": "%s на повну", "dpsmore": "Більше %s", "dpsslow": "Повільніше %s", "dpsstop": "Стоп %s"}
for _form, _word in (("written", "ДПС"), ("dipies", "ді-пі-ес"), ("latin", "DPS")):
    VARIANTS.append({"id": "el4-m-alex-dps-%s" % _form, "label": "m-alex, DPS: %s" % _word,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": list(_DPS), "override": {k: t % _word for k, t in _DPS.items()}})
for _form, _text, _extra in (("seed1", "Спис", {"seed": 1}), ("seed2", "Спис", {"seed": 2}),
                             ("seed3", "Спис", {"seed": 3}), ("dot", "Спис.", None), ("bang", "Спис!", None)):
    VARIANTS.append({"id": "el4-m-alex-spear-%s" % _form, "label": "m-alex, spear: %s" % _form,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": ["spear"], "override": {"spear": _text}, "extra": _extra})
# IPA [w] in "вперед" drops the "в" ("перед, перед").
for _form, _text in (("plain", "Вперед! Вперед! Вперед!"), ("u", "Уперед, уперед, уперед!"),
                     ("ipa-v", "/ʋpɛˈrɛd/, /ʋpɛˈrɛd/, /ʋpɛˈrɛd/!")):
    VARIANTS.append({"id": "el4-m-alex-go-%s" % _form, "label": "m-alex, com_go: %s" % _form,
                     "engine": "elevenlabs", "model": "eleven_v4", "voice": LIBRARY_VOICES["m-alex"],
                     "keys": ["com_go"], "override": {"com_go": _text}})
# Library voices need a paid plan over the API (402 paid_plan_required on the free tier).
# Premade voices do not, but none of them is verified for Ukrainian.
PREMADE_VOICES = {
    "voice-jessica": "cgSgspJ2msm6clMCkdW9",
    "voice-bella": "hpp4J3VqNfWAUOO0d1Us",
    "voice-charlie": "IKne3meq5aSn9XLyUdCD",
    "voice-harry": "SOYHLrjzK2X1ezoPC6cr",
}
for _vid, _voice in sorted({**UKRAINIAN_VOICES, **PREMADE_VOICES}.items()):
    VARIANTS.append(dict(V3, id=_vid, label="ElevenLabs v3: %s" % _vid[6:],
                         voice=_voice, keys=ENGINE_KEYS))
# Azure's other Ukrainian voice, and multilingual voices told to speak Ukrainian.
VARIANTS += [
    {"id": "azure-ostap", "label": "Azure uk-UA-OstapNeural", "engine": "azure",
     "voice": "uk-UA-OstapNeural", "keys": ENGINE_KEYS},
    {"id": "azure-ava-uk", "label": "Azure Ava Multilingual, uk-UA", "engine": "azure",
     "voice": "en-US-AvaMultilingualNeural", "lang": "uk-UA", "keys": ENGINE_KEYS},
    {"id": "azure-andrew-uk", "label": "Azure Andrew Multilingual, uk-UA", "engine": "azure",
     "voice": "en-US-AndrewMultilingualNeural", "lang": "uk-UA", "keys": ENGINE_KEYS},
]

# Google Cloud TTS: every female uk-UA Chirp 3 HD voice, and Gemini TTS steered by a
# prompt. Auth is the gcloud ADC login, billed to GOOGLE_PROJECT.
CHIRP_FEMALE = [
    "Achernar", "Aoede", "Autonoe", "Callirrhoe", "Despina", "Erinome", "Gacrux",
    "Kore", "Laomedeia", "Leda", "Pulcherrima", "Sulafat", "Vindemiatrix", "Zephyr",
]
CHIRP_MALE = [
    "Achird", "Algenib", "Algieba", "Alnilam", "Charon", "Enceladus", "Fenrir", "Iapetus",
    "Orus", "Puck", "Rasalgethi", "Sadachbia", "Sadaltager", "Schedar", "Umbriel", "Zubenelgenubi",
]
VARIANTS += [
    {"id": "chirp-%s" % name.lower(), "label": "Google Chirp 3 HD %s" % name,
     "engine": "google", "voice": "uk-UA-Chirp3-HD-%s" % name, "keys": ENGINE_KEYS}
    for name in CHIRP_FEMALE + CHIRP_MALE
]
GEMINI_PROMPT = "Коротка бойова команда в рейді: чітко, впевнено, енергійно, без пауз."
VARIANTS += [
    {"id": "gemini-%s" % name.lower(), "label": "Gemini 2.5 Pro TTS %s" % name,
     "engine": "google", "voice": name, "model": "gemini-2.5-pro-tts",
     "prompt": GEMINI_PROMPT, "keys": ENGINE_KEYS}
    for name in ("Kore", "Zephyr", "Aoede", "Leda")
]
# The combat prompt garbled single words; this isolates the prompt as the cause or not.
VARIANTS.append({
    "id": "gemini-aoede-neutral", "label": "Gemini 2.5 Pro TTS Aoede, neutral prompt",
    "engine": "google", "voice": "Aoede", "model": "gemini-2.5-pro-tts",
    "prompt": "Читай текст дослівно українською мовою. Природний розмовний голос, "
              "чітка артикуляція, рівна інтонація, звичайний темп.",
    "keys": ENGINE_KEYS})

# The licensed route to the voice the pack ships with.
VARIANTS += [
    {"id": "azure-polina", "label": "Azure uk-UA-PolinaNeural - whole pack",
     "engine": "azure", "voice": "uk-UA-PolinaNeural", "keys": "all"},
]


def table():
    """key -> (english source line, written Ukrainian, what the engine should hear).

    The fourth column exists because those last two are not always the same string.
    "ДПС" is spelled correctly and read aloud as an expanded government acronym, so the
    row keeps its spelling and hands the engine "де-пе-ес" instead.
    """
    rows = {}
    for name in ("ua_table.tsv", "events_table.tsv"):
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3:
                    spoken = parts[3].strip() if len(parts) > 3 else ""
                    rows[parts[0]] = (parts[1], parts[2], spoken or parts[2])
    return rows


def keys_of(variant, rows):
    """A variant covers either a hand-picked list or the whole pack."""
    if variant["keys"] == "all":
        return list(rows)
    return variant["keys"]


def text_for(variant, key, spoken):
    text = variant.get("override", {}).get(key, spoken)
    for written, heard in variant.get("spoken", {}).items():
        text = re.sub(r"(?<!\w)%s(?!\w)" % re.escape(written), heard, text, flags=re.IGNORECASE)
    return text


def eleven(text, model, language_code, dest, voice=MATILDA, extra=None):
    payload = {"text": text, "model_id": model, **(extra or {})}
    if language_code:
        payload["language_code"] = language_code
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_128" % voice,
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(dest, "wb").write(r.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            print("FAIL %s: %d %s" % (dest, e.code, e.read()[:200].decode("utf-8", "replace")))
            return False
        except Exception as e:  # network hiccup
            print("RETRY %s: %s" % (dest, e))
            time.sleep(5)
    return False


def azure(text, voice, dest, style=None, rate=None, lang=None):
    """Official Azure Speech, the licensed route to the same voice edge-tts borrows."""
    inner = text
    if lang:
        inner = '<lang xml:lang="%s">%s</lang>' % (lang, inner)
    if rate:
        inner = '<prosody rate="%s">%s</prosody>' % (rate, inner)
    if style:
        inner = '<mstts:express-as style="%s">%s</mstts:express-as>' % (style, inner)
    ssml = ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="uk-UA">'
            '<voice name="%s">%s</voice></speak>' % (voice, inner))
    req = urllib.request.Request(
        "https://%s.tts.speech.microsoft.com/cognitiveservices/v1" % AZURE_REGION,
        data=ssml.encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": AZURE_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm",
            "User-Agent": "dbm-vp-uk",
        })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(dest, "wb").write(r.read())
            return True
        except urllib.error.HTTPError as e:
            # The free tier's request cap is low, so throttling is expected, not an error.
            if e.code in (429, 503):
                time.sleep(10 * (attempt + 1))
                continue
            print("FAIL %s: %d %s" % (dest, e.code, e.read()[:200].decode("utf-8", "replace")))
            return False
        except Exception as e:
            print("RETRY %s: %s" % (dest, e))
            time.sleep(5)
    return False


GOOGLE_PROJECT = "project-22d39352-f39d-4ca1-bcc"
GCLOUD = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                      r"Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")
_GOOGLE_TOKEN = []


def google(text, voice, dest, model=None, prompt=None):
    """Google Cloud Text-to-Speech: Chirp 3 HD by voice name, Gemini TTS by model name."""
    import base64
    if not _GOOGLE_TOKEN:
        _GOOGLE_TOKEN.append(subprocess.run(
            [GCLOUD, "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, check=True).stdout.strip())
    body = {"input": {"text": text}, "voice": {"languageCode": "uk-UA", "name": voice},
            "audioConfig": {"audioEncoding": "LINEAR16"}}
    if model:
        body["voice"]["modelName"] = model
    if prompt:
        body["input"]["prompt"] = prompt
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + _GOOGLE_TOKEN[0],
                 "x-goog-user-project": GOOGLE_PROJECT,
                 "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(dest, "wb").write(base64.b64decode(json.load(r)["audioContent"]))
            return True
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(10 * (attempt + 1))
                continue
            print("FAIL %s: %d %s" % (dest, e.code, e.read()[:300].decode("utf-8", "replace")))
            return False
        except Exception as e:
            print("RETRY %s: %s" % (dest, e))
            time.sleep(5)
    return False


def edge(text, voice, dest):
    r = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice,
                        "--text", text, "--write-media", dest],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL %s: %s" % (dest, r.stderr[:200]))
        return False
    return True


# Neural voices pad a clip with silence - Azure's Polina averages 0.17 s in front and
# 0.90 s behind, against 1.04 s of actual speech. In a boss-warning pack the front
# padding is a late warning and the back padding is nothing at all, so both go.
TRIM = ("silenceremove=start_periods=1:start_silence=0.02:start_threshold=-45dB:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_silence=0.10:start_threshold=-45dB:detection=peak,"
        "areverse")


def to_ogg(src, ogg):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", TRIM,
                        "-c:a", "libvorbis", "-q:a", "4", "-ar", "44100", ogg],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG FAIL %s: %s" % (ogg, r.stderr[:200]))
        return False
    return True


def render(variant, rows):
    out = os.path.join(VARIANTS_DIR, variant["id"])
    texts = {}
    for key in keys_of(variant, rows):
        sent = text_for(variant, key, rows[key][2])
        texts[key] = sent
        ogg = os.path.join(out, key + ".ogg")
        os.makedirs(os.path.dirname(ogg), exist_ok=True)
        if os.path.exists(ogg) and os.path.getsize(ogg) > 0:
            continue
        raw = ogg[:-4] + (".wav" if variant["engine"] in ("azure", "google") else ".mp3")
        if variant["engine"] == "elevenlabs":
            ok = eleven(sent, variant["model"], variant.get("language_code"), raw,
                        variant.get("voice", MATILDA), variant.get("extra"))
        elif variant["engine"] == "azure":
            ok = azure(sent, variant["voice"], raw, variant.get("style"), variant.get("rate"),
                       variant.get("lang"))
        elif variant["engine"] == "google":
            ok = google(sent, variant["voice"], raw, variant.get("model"), variant.get("prompt"))
        else:
            ok = edge(sent, variant["voice"], raw)
        if ok and to_ogg(raw, ogg):
            print("  %s/%s" % (variant["id"], key))
        os.path.exists(raw) and os.remove(raw)
        time.sleep(0.3)
    return texts


RETIRED = {
    # Lost the engine round: an American-accent source voice reading Ukrainian.
    "turbo-uk", "v3", "edge-polina",
    # Capitalised stress hints won nothing and later proved to pull stress the wrong way.
    "v3-caps",
    # The wording round is settled; its picks live in the table now.
    "jargon", "plain-words",
    # The same voice through the browser's read-aloud endpoint: fine for listening,
    # not something a published pack may be built on.
    "polina-all",
}
# v2 renders only on request, for a voice whose v4 clips run too long.
RETIRED |= {"el2-" + _name for _name in LIBRARY_VOICES}


def main():
    wanted = sys.argv[1:]
    rows = table()
    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8"))
    for variant in VARIANTS:
        if wanted and variant["id"] not in wanted:
            continue
        if variant["id"] in RETIRED and not wanted:
            continue
        if variant["engine"] == "elevenlabs" and not ELEVEN_KEY:
            print("skip %s: ELEVENLABS_API_KEY not set" % variant["id"])
            continue
        print(variant["id"])
        texts = render(variant, rows)
        entry = {k: v for k, v in variant.items() if k not in ("keys", "override", "spoken")}
        entry["texts"] = texts
        manifest[variant["id"]] = entry
    os.makedirs(VARIANTS_DIR, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("manifest: %s (%d variants)" % (MANIFEST, len(manifest)))


if __name__ == "__main__":
    main()
