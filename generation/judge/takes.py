"""Render several takes of one pack line on m-alex and rank them by phones and words heard.

Run: python takes.py <key> <seeds> <text> [<text> ...]
Takes land in takes/<key>/; nothing is copied into the pack.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
import g2p
import hearphones
from phoncheck import align, classes

sys.path.insert(0, hearphones.GEN)
import bakeoff
import hear
import models
from check_audio import score

speed = next((float(a.split("=")[1]) for a in sys.argv if a.startswith("--speed=")), None)
args = [a for a in sys.argv[1:] if not a.startswith("--")]
key, seeds, sent_texts = args[0], int(args[1]), args[2:]
rows = bakeoff.table()
written = rows[key][2]
expected = classes(g2p.phones(written))
out_dir = os.path.join(HERE, "takes", key.replace("/", "_"))
os.makedirs(out_dir, exist_ok=True)
voice = bakeoff.LIBRARY_VOICES["m-alex"]

results = []
for text in sent_texts:
    for seed in range(1, seeds + 1):
        tag = hashlib.md5(text.encode("utf-8")).hexdigest()[:10] + ("-x%s" % speed if speed else "")
        ogg = os.path.join(out_dir, "%s-s%d.ogg" % (tag, seed))
        extra = {"seed": seed}
        if speed:
            extra["voice_settings"] = {"stability": 0.5, "similarity_boost": 0.75, "speed": speed}
        if not os.path.exists(ogg):
            mp3 = ogg[:-4] + ".mp3"
            if not (bakeoff.eleven(text, "eleven_v4", None, mp3, voice, extra) and bakeoff.to_ogg(mp3, ogg)):
                continue
            os.remove(mp3)
        phones = hearphones.heard(ogg)
        errors, ops = align(expected, classes(phones))
        words = hear.transcribe(ogg, models.ASR)
        stress = hear.transcribe(ogg, models.STRESS)
        length = len(hear._audio(ogg)) / 16000
        results.append((errors, -score(written, words, stress), ogg, text, seed, " ".join(ops), phones, words, length))

results.sort()
for e, m, ogg, text, seed, ops, phones, words, length in results:
    print("%.1f  match %.2f  %.2fs  %-28s seed %d  %-18s heard: %s | %s  %s" % (
        e, -m, length, text, seed, ops, words, phones, os.path.basename(ogg)))
print("BEST", results[0][2])
