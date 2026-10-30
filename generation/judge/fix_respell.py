"""Second pass for any voice: lines the seed loop could not fix get respelled candidates.

Known spellings are the ones that passed on m-alex; any other line tries "!" and "." endings.
Run: python fix_respell.py <variant>
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
variant = next(v for v in bakeoff.VARIANTS if v["id"] == VID)
rows = bakeoff.table()
SEEDS = (201, 202)
SKIP = {"wrathaura"}  # гні́вна (en.wiktionary uk-IPA): the judge asks for the wrong stress
ZMINY = "/zmʲiˈnɪ/ "
KNOWN = {
    "1695gorak": ["Gorak на човні!", "Gorak на човні"],
    "1695ukurogg": ["Ukurogg на човні", "Ukurogg на човні!"],
    "attacktotem": ["Атакуй /toˈtɛm/", "Атакуй /toˈtɛm/!"],
    "breaktormentfirst": ["Розбивай /ˈmuku/ першим"],
    "breaktormentthird": ["Розбивай /ˈmuku/ третім"],
    "com_go": ["Впе-ред, впе-ред, впе-ред!", "Вперед! Вперед! Вперед!"],
    "spear": ["Спис!", "Спис."],
    "fearsoon": ["Скоро страх!", "/ˈskɔrɔ/ страх"],
    "breakvine": ["Розірви лозу!"],
}
for key, rest in (("changecolor", "колір"), ("changemoon", "місяць"), ("changetarget", "ціль"),
                  ("changeplatform", "платформу")):
    KNOWN[key] = [ZMINY + rest, ZMINY + rest + "!"]

verdicts = {r["key"]: r["verdict"] for r in csv.DictReader(
    open(os.path.join(HERE, "judge-%s.tsv" % VID), encoding="utf-8"), delimiter="\t")}
log = list(csv.DictReader(open(os.path.join(HERE, "fixloop-%s.tsv" % VID), encoding="utf-8"), delimiter="\t"))
fixed = {r["key"] for r in log if r["verdict"] == "pass"}
todo = [k for k in rows if verdicts.get(k) != "pass" and k not in fixed and k not in SKIP]
print("%d lines" % len(todo), flush=True)


def candidates(key):
    if key in KNOWN:
        return KNOWN[key]
    base = bakeoff.text_for(variant, key, rows[key][2]).rstrip("!.")
    return [base + "!", base + "."]


def run(key):
    try:
        text, note = expected(key, rows)
        pack = os.path.join(bakeoff.VARIANTS_DIR, VID, key + ".ogg")
        if key not in verdicts:  # never judged
            r = judge(pack, text, note)
            if r.get("verdict") == "pass":
                return key, "as is", []
        out = os.path.join(HERE, "takes", VID, key.replace("/", "_"))
        os.makedirs(out, exist_ok=True)
        tried = []
        for i, sent in enumerate(candidates(key)):
            for seed in SEEDS:
                ogg = os.path.join(out, "rs-%d-s%d.ogg" % (i, seed))
                if not os.path.exists(ogg):
                    mp3 = ogg[:-4] + ".mp3"
                    if not (bakeoff.eleven(sent, variant["model"], None, mp3, variant["voice"], {"seed": seed})
                            and bakeoff.to_ogg(mp3, ogg)):
                        continue
                    os.remove(mp3)
                r = judge(ogg, text, note)
                tried.append(("%s seed %d" % (sent, seed), r.get("verdict"), " | ".join(r.get("problems", []))))
                if r.get("verdict") == "pass":
                    shutil.copyfile(ogg, pack)
                    return key, tried[-1][0], tried
        return key, None, tried
    except Exception as e:
        return key, None, [("error", "error", str(e)[:150])]


with concurrent.futures.ThreadPoolExecutor(3) as pool, \
        open(os.path.join(HERE, "respell-%s.tsv" % VID), "w", encoding="utf-8") as fh:
    fh.write("key\tcandidate\tverdict\tproblems\n")
    won = 0
    for key, label, tried in pool.map(run, todo):
        for c, v, p in tried:
            fh.write("%s\t%s\t%s\t%s\n" % (key, c, v, p.replace("\t", " ")))
        fh.flush()
        won += bool(label)
        print("%-20s %s" % (key, "PASS " + label if label else "fail"), flush=True)
    print("fixed %d of %d" % (won, len(todo)))
