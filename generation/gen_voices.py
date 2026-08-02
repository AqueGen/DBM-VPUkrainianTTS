# Generate DBM Ukrainian voice pack via ElevenLabs (Matilda, multilingual v2).
# Reads ua_table.tsv (file<TAB>en<TAB>ua), writes mp3 to out_mp3/, ogg to out_ogg/.
# Resumable: skips files that already have a non-empty ogg.
import os, sys, time, subprocess, urllib.request, urllib.error, json

SP = os.path.dirname(os.path.abspath(__file__))
VOICE_ID = "XrExE9yKIg1WjnnlVkGX"  # Matilda
# SHORT_MODE: regen 1-2 word phrases with turbo + forced uk (multilingual_v2 misreads
# short Cyrillic text as Russian and has no language_code support)
SHORT_MODE = os.environ.get("GEN_SHORT") == "1"
MODEL = "eleven_turbo_v2_5" if SHORT_MODE else "eleven_multilingual_v2"
KEY = os.environ.get("ELEVENLABS_API_KEY")
if not KEY:
    sys.exit("ELEVENLABS_API_KEY not set")

TABLE = os.environ.get("GEN_TABLE", "ua_table.tsv")

rows = [l.split("\t") for l in open(os.path.join(SP, TABLE), encoding="utf-8").read().strip().split("\n")]
if SHORT_MODE:
    rows = [r for r in rows if len(r[2].split()) <= 2]
    for name, _, _ in rows:  # force regen
        for p in (os.path.join(SP, "out_ogg", name + ".ogg"), os.path.join(SP, "out_mp3", name + ".mp3")):
            if os.path.exists(p):
                os.remove(p)
for name, _, _ in rows:  # subfolders used by the table (count, Thogar, events, ...)
    for base in ("out_mp3", "out_ogg"):
        os.makedirs(os.path.dirname(os.path.join(SP, base, name + ".ogg")), exist_ok=True)

def tts(text, dest):
    payload = {"text": text, "model_id": MODEL}
    if SHORT_MODE:
        payload["language_code"] = "uk"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(dest, "wb").write(r.read())
            return True
        except urllib.error.HTTPError as e:
            msg = e.read()[:300]
            if e.code == 429:
                time.sleep(10 * (attempt + 1)); continue
            print(f"FAIL {dest}: {e.code} {msg}", flush=True)
            return False
        except Exception as e:
            print(f"RETRY {dest}: {e}", flush=True)
            time.sleep(5)
    return False

done = fail = 0
for i, (name, en, ua) in enumerate(rows):
    ogg = os.path.join(SP, "out_ogg", name + ".ogg")
    mp3 = os.path.join(SP, "out_mp3", name + ".mp3")
    if os.path.exists(ogg) and os.path.getsize(ogg) > 0:
        done += 1; continue
    if not (os.path.exists(mp3) and os.path.getsize(mp3) > 0):
        if not tts(ua, mp3):
            fail += 1; continue
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
                        "-c:a", "libvorbis", "-q:a", "4", "-ar", "44100", ogg],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FFMPEG FAIL {name}: {r.stderr[:200]}", flush=True)
        fail += 1; continue
    done += 1
    if done % 25 == 0:
        print(f"progress: {done}/{len(rows)} (fail {fail})", flush=True)
    time.sleep(0.3)  # ponytail: gentle pacing, free tier concurrency is low

print(f"DONE: {done}/{len(rows)}, failed: {fail}", flush=True)
