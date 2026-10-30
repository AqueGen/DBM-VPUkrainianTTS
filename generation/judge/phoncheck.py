"""Expected (espeak uk) vs heard (phone recogniser) per clip, aligned on coarse phone classes.

Stress and fine detail are dropped on purpose: espeak's Ukrainian stress is often wrong and the
recogniser blurs voicing and palatalisation. What survives is what a listener calls a wrong
sound: a missing or extra sound, o heard as a, an added syllable.

Run: python phoncheck.py <variant> [<variant> ...]   writes phoncheck-<variant>.tsv here
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g2p
import hearphones

sys.path.insert(0, hearphones.GEN)
import bakeoff

CLASS = {}
for cls, members in {
    "A": "a ɑ ʌ ɐ æ", "O": "o ɔ ɒ", "E": "e ɛ ə ɜ", "I": "i ɪ ɨ y j ʏ", "U": "u ʊ",
    "V": "v β ʋ w f ɸ", "P": "p b", "T": "t d c ɟ", "K": "k g ɡ", "S": "s z ɕ ʑ", "Ʃ": "ʃ ʒ",
    "H": "x h ɦ ɣ χ", "L": "l ʎ ɫ ɭ", "N": "n ɲ ŋ", "M": "m", "R": "r ɾ ʀ ʁ ɹ",
}.items():
    for m in members.split():
        CLASS[m] = cls
DROP = set("ˈˌːˑ̪ʲ̃ |")


def classes(phones):
    out = []
    for tok in phones.split():
        tok = "".join(c for c in tok if c not in DROP)
        if not tok:
            continue
        # affricates may come as one token or two; split so both sides agree
        for ch in ([tok] if tok in CLASS else list(tok)):
            if ch in CLASS:
                out.append(CLASS[ch])
            elif ch.strip() and ch not in DROP:
                out.append("?" + ch)
    return out


# Unstressed е and и merge in normal Ukrainian speech, and й is a short glide the recogniser
# drops or adds at will; neither is what a listener hears as a wrong sound.
def sub(x, y):
    return 0 if x == y or {x, y} == {"E", "I"} else 1


def indel(x):
    return 0.5 if x == "I" else 1


def align(a, b):
    n, m = len(a), len(b)
    d = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d[i][0] = d[i - 1][0] + indel(a[i - 1])
    for j in range(1, m + 1):
        d[0][j] = d[0][j - 1] + indel(b[j - 1])
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + indel(a[i - 1]), d[i][j - 1] + indel(b[j - 1]),
                          d[i - 1][j - 1] + sub(a[i - 1], b[j - 1]))
    i, j, ops = n, m, []
    while i or j:
        if i and j and d[i][j] == d[i - 1][j - 1] + sub(a[i - 1], b[j - 1]):
            if sub(a[i - 1], b[j - 1]):
                ops.append("%s>%s" % (a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i and d[i][j] == d[i - 1][j] + indel(a[i - 1]):
            if indel(a[i - 1]) == 1:
                ops.append("-%s" % a[i - 1])
            i -= 1
        else:
            if indel(b[j - 1]) == 1:
                ops.append("+%s" % b[j - 1])
            j -= 1
    return d[n][m], list(reversed(ops))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = bakeoff.table()
    manifest = json.load(open(bakeoff.MANIFEST, encoding="utf-8"))
    for vid in sys.argv[1:]:
        lines = ["key\terrors\trate\tops\ttext\texpected\theard"]
        for key in manifest[vid]["texts"]:
            ogg = os.path.join(bakeoff.VARIANTS_DIR, vid, key + ".ogg")
            if not os.path.exists(ogg) or key not in rows:
                continue
            text = rows[key][2]
            exp, got = g2p.phones(text), hearphones.heard(ogg)
            ce, cg = classes(exp), classes(got)
            errors, ops = align(ce, cg)
            lines.append("%s\t%.1f\t%.2f\t%s\t%s\t%s\t%s" % (
                key, errors, errors / max(1, len(ce)), " ".join(ops), text, exp, got))
        out = os.path.join(HERE, "phoncheck-%s.tsv" % vid)
        open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(out, len(lines) - 1, flush=True)


if __name__ == "__main__":
    main()
