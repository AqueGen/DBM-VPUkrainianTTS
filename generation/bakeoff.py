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
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS_DIR = os.path.join(HERE, "variants")
MANIFEST = os.path.join(VARIANTS_DIR, "manifest.json")

ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
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
    dict(TURBO, id="jargon", label="wording: as shipped (jargon)", keys=JARGON_KEYS),
    dict(TURBO, id="plain-words", label="wording: no borrowed words",
         keys=JARGON_KEYS, override=PLAIN_WORDING),
]

# Round 3 - the voice itself. Matilda is an American-accent source voice, and ElevenLabs
# states that a voice's own accent leaks into multilingual output, so a Ukrainian-native
# voice may fix at the root what respelling and stress hints fight downstream.
# Fill in ids from the ElevenLabs voice library (Voices -> Library -> language Ukrainian)
# and rerun: python generation/bakeoff.py voice-<name>
UKRAINIAN_VOICES = {
    # "voice-<short name>": "<voice_id>",
}
for _vid, _voice in sorted(UKRAINIAN_VOICES.items()):
    VARIANTS.append(dict(TURBO, id=_vid, label="voice: %s (turbo, forced uk)" % _vid,
                         voice=_voice, keys=ENGINE_KEYS))

# Free, local, and trained on Ukrainian speech rather than adapted to it.
VARIANTS += [
    {"id": "piper-tetiana", "label": "Piper tetiana (local, free)", "engine": "piper",
     "voice": "tetiana", "keys": ENGINE_KEYS},
    {"id": "piper-lada", "label": "Piper lada (local, free)", "engine": "piper",
     "voice": "lada", "keys": ENGINE_KEYS},
    # Same speakers, a different model: multi-speaker, CC0 data, 22 kHz.
    {"id": "piper-multi-tetiana", "label": "Piper ukrainian_tts / tetiana (local, free)",
     "engine": "piper", "voice": "ukrainian_tts", "speaker": 2, "keys": ENGINE_KEYS},
    {"id": "piper-multi-lada", "label": "Piper ukrainian_tts / lada (local, free)",
     "engine": "piper", "voice": "ukrainian_tts", "speaker": 0, "keys": ENGINE_KEYS},
]


def table():
    rows = {}
    for name in ("ua_table.tsv", "events_table.tsv"):
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3:
                    rows[parts[0]] = (parts[1], parts[2])
    return rows


def text_for(variant, key, ua):
    return variant.get("override", {}).get(key, ua)


def eleven(text, model, language_code, dest, voice=MATILDA):
    payload = {"text": text, "model_id": model}
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


_PIPER_CACHE = {}


def piper(text, voice, dest, speaker=None):
    """Local synthesis with a Piper voice trained on Ukrainian. Writes a wav."""
    import wave

    import models
    from piper import PiperVoice

    if voice not in _PIPER_CACHE:
        _PIPER_CACHE[voice] = PiperVoice.load(models.piper_voice(voice))
    loaded = _PIPER_CACHE[voice]
    config = None
    if speaker is not None:
        from piper.config import SynthesisConfig
        config = SynthesisConfig(speaker_id=speaker)
    with wave.open(dest, "wb") as wav:
        loaded.synthesize_wav(text, wav, syn_config=config)
    return True


def edge(text, voice, dest):
    r = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice,
                        "--text", text, "--write-media", dest],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL %s: %s" % (dest, r.stderr[:200]))
        return False
    return True


def to_ogg(mp3, ogg):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
                        "-c:a", "libvorbis", "-q:a", "4", "-ar", "44100", ogg],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FFMPEG FAIL %s: %s" % (ogg, r.stderr[:200]))
        return False
    return True


def render(variant, rows):
    out = os.path.join(VARIANTS_DIR, variant["id"])
    texts = {}
    for key in variant["keys"]:
        ua = rows[key][1]
        sent = text_for(variant, key, ua)
        texts[key] = sent
        ogg = os.path.join(out, key + ".ogg")
        os.makedirs(os.path.dirname(ogg), exist_ok=True)
        if os.path.exists(ogg) and os.path.getsize(ogg) > 0:
            continue
        raw = ogg[:-4] + (".wav" if variant["engine"] == "piper" else ".mp3")
        if variant["engine"] == "elevenlabs":
            ok = eleven(sent, variant["model"], variant.get("language_code"), raw,
                        variant.get("voice", MATILDA))
        elif variant["engine"] == "piper":
            ok = piper(sent, variant["voice"], raw, variant.get("speaker"))
        else:
            ok = edge(sent, variant["voice"], raw)
        if ok and to_ogg(raw, ogg):
            print("  %s/%s" % (variant["id"], key))
        os.path.exists(raw) and os.remove(raw)
        time.sleep(0.3)
    return texts


def main():
    wanted = sys.argv[1:]
    rows = table()
    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8"))
    for variant in VARIANTS:
        if wanted and variant["id"] not in wanted:
            continue
        if variant["engine"] == "elevenlabs" and not ELEVEN_KEY:
            print("skip %s: ELEVENLABS_API_KEY not set" % variant["id"])
            continue
        print(variant["id"])
        texts = render(variant, rows)
        entry = {k: v for k, v in variant.items() if k not in ("keys", "override")}
        entry["texts"] = texts
        manifest[variant["id"]] = entry
    os.makedirs(VARIANTS_DIR, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("manifest: %s (%d variants)" % (MANIFEST, len(manifest)))


if __name__ == "__main__":
    main()
