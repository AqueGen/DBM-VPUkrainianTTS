#!/usr/bin/env python3
"""Listen to every clip with two local models and rank the rows worth a human ear.

What it can decide: whether the words that came out are the words that went in. That
catches a mangled word ("Вайп" coming back as "вайпи"), a swallowed one, and a clipped
ending - the defects that change *which* word was said.

What it cannot decide: whether a correctly recognised word carries a Ukrainian or a
Russian colouring, and whether the stress sits where the language puts it. The stress
model's output is reported beside each row because it demonstrably follows the audio
rather than a lexicon - "Погнали" came back as "п+огнали", reproducing the defect a
human heard - but with no stress dictionary to compare against, it is evidence for a
person to read, not a verdict.

Run:  python generation/check_audio.py [variant]     (default: azure-polina)
Writes generation/audio-check.tsv, worst first.
"""
import difflib
import json
import os
import re
import sys

import hear
import models

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "azure-polina"
REPORT = os.path.join(HERE, "audio-check.tsv")

APOSTROPHES = "'’ʼ`"


def normalise(text):
    """Compare what was said, not how it was punctuated."""
    text = text.lower().replace("ґ", "г")
    text = "".join(" " if c in APOSTROPHES else c for c in text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def similarity(expected, heard):
    return difflib.SequenceMatcher(None, normalise(expected), normalise(heard)).ratio()


def score(sent, heard, stress):
    """Believe a row is broken only when both models disagree with the text.

    Either model alone produces false alarms on short clips: "П'ять" came back empty
    from the ASR while the stress model heard п'+ять perfectly, and "Кинь смолоскип"
    was mangled by the ASR and transcribed correctly by the other. Taking the better of
    the two leaves the rows where the audio, not the recogniser, is the problem.
    """
    return max(similarity(sent, heard), similarity(sent, stress.replace("+", "")))


def main():
    manifest = json.load(open(os.path.join(HERE, "variants", "manifest.json"), encoding="utf-8"))
    if VARIANT not in manifest:
        raise SystemExit("no such variant: %s" % VARIANT)
    texts = manifest[VARIANT]["texts"]

    rows = []
    for i, (key, sent) in enumerate(sorted(texts.items()), 1):
        clip = os.path.join(HERE, "variants", VARIANT, key + ".ogg")
        if not os.path.isfile(clip):
            continue
        heard = hear.transcribe(clip, models.ASR)
        stress = hear.transcribe(clip, models.STRESS)
        rows.append((score(sent, heard, stress), key, sent, heard, stress))
        if i % 25 == 0:
            print("  %d/%d" % (i, len(texts)), flush=True)

    rows.sort()
    with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("match\tkey\tsent\theard\tstress\n")
        for match, key, sent, heard, stress in rows:
            fh.write("%.2f\t%s\t%s\t%s\t%s\n" % (match, key, sent, heard, stress))

    # Requiring both models to disagree makes 0.75 unreachable in practice - on the first
    # full run nothing fell below it. The output is a ranking to listen down, not a gate.
    bad = [r for r in rows if r[0] < 0.90]
    print("\n%s: %d clips, %d worth an ear (below 0.90)" % (VARIANT, len(rows), len(bad)))
    for score, key, sent, heard, _ in bad[:25]:
        print("  %.2f  %-18s sent %-34s heard %s" % (score, key, sent, heard))
    print("\nfull report: %s" % REPORT)


if __name__ == "__main__":
    main()
