"""For every clip the judge failed (or never judged): render takes with new seeds until one passes.

A passing take replaces the pack clip. Every attempt is logged to fixloop-<variant>.tsv.
Run: python fix_loop.py <variant> [max takes per line]
"""
import concurrent.futures
import csv
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
from judge import bakeoff, judge
from judge_pack import expected

VID = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 4
variant = next(v for v in bakeoff.VARIANTS if v["id"] == VID)
rows = bakeoff.table()
verdicts = {r["key"]: r for r in csv.DictReader(open(os.path.join(HERE, "judge-%s.tsv" % VID), encoding="utf-8"),
                                                delimiter="\t")}
log_path = os.path.join(HERE, "fixloop-%s.tsv" % VID)
if not os.path.exists(log_path):
    open(log_path, "w", encoding="utf-8").write("key\tseed\tverdict\tsent\tproblems\n")
logged = list(csv.DictReader(open(log_path, encoding="utf-8"), delimiter="\t"))
# a line is settled once a take passed or every take was tried
settled = {r["key"] for r in logged if r["verdict"] == "pass"} | {
    k for k in {r["key"] for r in logged} if sum(r["key"] == k for r in logged) >= MAX}
todo = [k for k in rows if (k not in verdicts or verdicts[k]["verdict"] != "pass") and k not in settled]
print("%d lines to fix" % len(todo), flush=True)


def fix(key):
    try:
        return attempt(key)
    except Exception as e:  # one bad line must not stop the rest; it is retried on the next run
        return key, None, "error " + str(e)[:150], "", []


def attempt(key):
    sent = bakeoff.text_for(variant, key, rows[key][2])
    text, note = expected(key, rows)
    pack_clip = os.path.join(bakeoff.VARIANTS_DIR, VID, key + ".ogg")
    if key not in verdicts:  # never judged: judge the current clip first
        r = judge(pack_clip, text, note)
        if r.get("verdict") == "pass":
            return key, 0, "pass", sent, []
    out_dir = os.path.join(HERE, "takes", key.replace("/", "_"))
    os.makedirs(out_dir, exist_ok=True)
    log = []
    for seed in range(101, 101 + MAX):
        ogg = os.path.join(out_dir, "fix-s%d.ogg" % seed)
        if not os.path.exists(ogg):
            mp3 = ogg[:-4] + ".mp3"
            if not (bakeoff.eleven(sent, variant["model"], None, mp3, variant["voice"], {"seed": seed})
                    and bakeoff.to_ogg(mp3, ogg)):
                continue
            os.remove(mp3)
        r = judge(ogg, text, note)
        log.append((seed, r.get("verdict"), " | ".join(r.get("problems", []))))
        if r.get("verdict") == "pass":
            shutil.copyfile(ogg, pack_clip)
            return key, seed, "pass", sent, log
    return key, None, "fail", sent, log


with concurrent.futures.ThreadPoolExecutor(3) as pool, open(log_path, "a", encoding="utf-8") as fh:
    fixed = 0
    for key, seed, verdict, sent, log in pool.map(fix, todo):
        for s, v, p in log:
            fh.write("%s\t%s\t%s\t%s\t%s\n" % (key, s, v, sent, p.replace("\t", " ").replace("\n", " ")))
        fh.flush()
        fixed += verdict == "pass"
        print("%-20s %s%s" % (key, verdict, " (seed %s)" % seed if seed else ""), flush=True)
    print("fixed %d of %d" % (fixed, len(todo)))
