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

# Phrases under test: the failure modes behind the flagged phrases (single word, wrong
# stress, Russian-sounding vowels, slang, abbreviation, long line with punctuation).
KEYS = [
    "uu", "thanks", "defensive", "kite", "aesoon",
    "bait", "harmonic", "crowdcontrol", "interruptbyeye", "Thogar/B2D3",
]

# Stress written as a capital letter on the stressed vowel - the one hint the engine is
# known to honour (a combining acute breaks it, see CLAUDE.md).
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

VARIANTS = [
    {
        "id": "turbo-uk",
        "label": "ElevenLabs turbo v2.5, forced uk",
        "engine": "elevenlabs",
        "model": "eleven_turbo_v2_5",
        "language_code": "uk",
        "text": "plain",
    },
    {
        "id": "v3",
        "label": "ElevenLabs v3, plain text",
        "engine": "elevenlabs",
        "model": "eleven_v3",
        "text": "plain",
    },
    {
        "id": "v3-caps",
        "label": "ElevenLabs v3, stress as a capital letter",
        "engine": "elevenlabs",
        "model": "eleven_v3",
        "text": "caps",
    },
    {
        "id": "edge-polina",
        "label": "edge-tts uk-UA-PolinaNeural (free)",
        "engine": "edge",
        "voice": "uk-UA-PolinaNeural",
        "text": "plain",
    },
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
    if variant["text"] == "caps":
        return CAPS_STRESS[key]
    return ua


def eleven(text, model, language_code, dest):
    payload = {"text": text, "model_id": model}
    if language_code:
        payload["language_code"] = language_code
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_128" % MATILDA,
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
    for key in KEYS:
        ua = rows[key][1]
        sent = text_for(variant, key, ua)
        texts[key] = sent
        ogg = os.path.join(out, key + ".ogg")
        os.makedirs(os.path.dirname(ogg), exist_ok=True)
        if os.path.exists(ogg) and os.path.getsize(ogg) > 0:
            continue
        mp3 = ogg[:-4] + ".mp3"
        if variant["engine"] == "elevenlabs":
            ok = eleven(sent, variant["model"], variant.get("language_code"), mp3)
        else:
            ok = edge(sent, variant["voice"], mp3)
        if ok and to_ogg(mp3, ogg):
            print("  %s/%s" % (variant["id"], key))
        os.path.exists(mp3) and os.remove(mp3)
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
        entry = {k: v for k, v in variant.items() if k != "text"}
        entry["texts"] = texts
        manifest[variant["id"]] = entry
    os.makedirs(VARIANTS_DIR, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("manifest: %s (%d variants)" % (MANIFEST, len(manifest)))


if __name__ == "__main__":
    main()
