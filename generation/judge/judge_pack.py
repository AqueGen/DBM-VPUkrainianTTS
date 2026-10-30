"""Judge every clip of a variant; writes judge-<variant>.tsv here. Resumes: judged keys are skipped."""
import concurrent.futures
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
from judge import bakeoff, judge

DPS = 'Note: "DPS" is meant as the English acronym (dee-pee-ess), spoken quickly as one unit.'


def expected(key, rows):
    text = rows[key][1].replace("ДПС", "DPS")
    return text, DPS if "DPS" in text else ""


def main(vid):
    rows = bakeoff.table()
    out = os.path.join(HERE, "judge-%s.tsv" % vid)
    done = set()
    if os.path.exists(out):
        done = {r["key"] for r in csv.DictReader(open(out, encoding="utf-8"), delimiter="\t")}
    else:
        open(out, "w", encoding="utf-8").write("key\tverdict\ttext\tproblems\n")
    keys = [k for k in rows if k not in done and os.path.exists(os.path.join(bakeoff.VARIANTS_DIR, vid, k + ".ogg"))]

    def one(key):
        text, note = expected(key, rows)
        try:
            r = judge(os.path.join(bakeoff.VARIANTS_DIR, vid, key + ".ogg"), text, note)
        except Exception as e:  # keep going; the key stays unjudged and is retried on the next run
            return key, None, text, str(e)[:200]
        return key, r.get("verdict"), text, " | ".join(r.get("problems", []))

    with concurrent.futures.ThreadPoolExecutor(8) as pool, open(out, "a", encoding="utf-8") as fh:
        for key, verdict, text, problems in pool.map(one, keys):
            if verdict:
                fh.write("%s\t%s\t%s\t%s\n" % (key, verdict, text, problems.replace("\t", " ").replace("\n", " ")))
                fh.flush()
            print(key, verdict or "ERROR " + problems, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
