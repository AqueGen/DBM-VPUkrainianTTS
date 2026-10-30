"""Ask the judge to compare every ElevenLabs voice side by side and pick the ones that fit WoW callouts.

Each voice gets one sample: four of the bake-off lines joined with short gaps. All samples go in
one request so the model compares them against each other, not one at a time.
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
import judge
from judge import bakeoff

LINES = list(bakeoff.ENGINE_KEYS)
VOICES = ["marlena", "mariya", "katerina-boyko", "vira", "alena", "tonya", "kira", "kateryna", "solomiya",
          "yaroslava", "anna", "ana", "sofiia", "alisa", "m-artem", "m-alex", "m-evgeniy", "m-bogdan"]
OUT = os.path.join(HERE, "samples10")
os.makedirs(OUT, exist_ok=True)


def sample(voice):
    dst = os.path.join(OUT, voice + ".ogg")
    if not os.path.exists(dst):
        clips = [os.path.join(bakeoff.VARIANTS_DIR, "el4-" + voice, k + ".ogg") for k in LINES]
        args, parts = [], []
        for i, c in enumerate(clips):
            args += ["-i", c]
            parts.append("[%d:a]apad=pad_dur=0.4[a%d]" % (i, i))
        graph = ";".join(parts) + ";" + "".join("[a%d]" % i for i in range(len(clips))) + \
            "concat=n=%d:v=0:a=1" % len(clips)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", graph,
                        "-ac", "1", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "4", dst], check=True)
    return dst


texts = [bakeoff.table()[k][1] for k in LINES]
parts = [{"text": (
    "You are choosing voices for a Ukrainian voice pack for Deadly Boss Mods in World of Warcraft. "
    "The pack shouts short warnings in the middle of raid and Mythic+ fights, over game music and "
    "effects, for hours of play. Each sample below is one voice saying the same ten lines: %s.\n"
    "Compare the voices against each other. Judge: clarity over a noisy fight, urgency without "
    "being shrill or tiring over hours, natural native Ukrainian pronunciation, fit with the fantasy "
    "game mood, and how fast the lines land. Ignore that voices differ in gender.\n"
    "Answer JSON: {\"female_ranking\": [{\"voice\": id, \"why\": text}, ...] best first (ids not starting "
    "with m-), \"male_ranking\": [...] best first (ids starting with m-), \"pick_female\": id, "
    "\"pick_male\": id, \"avoid\": [{\"voice\": id, \"why\": text}]}") % " / ".join(texts)}]
order = VOICES[::-1] if "--reverse" in sys.argv else VOICES
for v in order:
    parts.append({"text": "Voice id: %s" % v})
    parts.append({"inlineData": {"mimeType": "audio/ogg",
                                 "data": base64.b64encode(open(sample(v), "rb").read()).decode()}})
body = {"contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
req = urllib.request.Request(judge.URL, data=json.dumps(body).encode("utf-8"), headers={
    "Authorization": "Bearer " + judge.token(), "x-goog-user-project": bakeoff.GOOGLE_PROJECT,
    "Content-Type": "application/json"})
out = json.load(urllib.request.urlopen(req, timeout=600))
answer = json.loads(out["candidates"][0]["content"]["parts"][-1]["text"])
open(os.path.join(HERE, "pick_voice%s.json" % ("-rev" if "--reverse" in sys.argv else "")), "w", encoding="utf-8").write(json.dumps(answer, ensure_ascii=False, indent=1))
print(json.dumps(answer, ensure_ascii=False, indent=1))
