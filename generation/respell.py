#!/usr/bin/env python3
"""Try several spellings of a mispronounced line and let the models pick the best one.

check_audio.py says which rows come out wrong. This one tries to fix them: each
candidate spelling is synthesised, run through both recognisers, and scored the same
way. The winner goes into its own column in the review page, next to what ships today.

The score measures whether a machine can make out the words, not whether they sound
good - a stiff-but-clear reading wins on points. So this proposes, the ear disposes.

Run:  python generation/respell.py            # render and score every candidate
      python generation/respell.py paranoiayou
"""
import json
import os
import subprocess
import sys

import bakeoff
import check_audio
import hear
import models

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANT = "azure-fixed"
OUT = os.path.join(HERE, "variants", VARIANT)

# Spellings to try for the rows the check ranked worst. The first entry of each list is
# what the pack says today, so a candidate has to beat it rather than merely differ.
CANDIDATES = {
    "paranoiayou": ["Параноя на тобі", "Паранойя на тобі", "Пара-ноя на тобі"],
    "wrathaura": ["Аура гніву", "Ау́ра гніву", "Гнівна аура", "Аура люті"],
    "peaceaura": ["Аура миру", "Ау́ра миру", "Мирна аура"],
    "devotionaura": ["Аура відданості", "Ау́ра відданості", "Віддана аура"],
    "attacktotem": ["Атакуй тотем", "Атакуй тоте́м", "Бий тотем", "Атакуй тотема"],
    "attackshield": ["Атакуй щит", "Атакуй щита", "Бий щит"],
    "findshield": ["Знайди щит", "Знайди щита", "Шукай щит"],
    "movetoegg": ["Іди до яйця", "Біжи до яйця", "Іди до яєць"],
    "throweyetank": ["Кинь око танку", "Кинь око танкові", "Кинь око до танка"],
    "events/pull": ["Пулимо", "Починаємо", "Стягуємо", "Тягнемо"],
    "melodic": ["Мелодія", "Мело́дія", "Мелодійна"],
    "transporter": ["Транспортер", "Транспорте́р", "Портал"],
}


def render(text, dest):
    raw = dest[:-4] + ".wav"
    if not bakeoff.azure(text, "uk-UA-PolinaNeural", raw):
        return False
    ok = bakeoff.to_ogg(raw, dest)
    if os.path.exists(raw):
        os.remove(raw)
    return ok


def seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def main():
    wanted = sys.argv[1:]
    winners = {}
    print("%-8s %-24s %5s %5s  %s" % ("score", "candidate", "sec", "", "heard"))
    for key, options in sorted(CANDIDATES.items()):
        if wanted and key not in wanted:
            continue
        print("\n%s" % key)
        scored = []
        for i, text in enumerate(options):
            clip = os.path.join(HERE, "variants", "_respell", key + "_%d.ogg" % i)
            os.makedirs(os.path.dirname(clip), exist_ok=True)
            if not os.path.exists(clip) and not render(text, clip):
                continue
            heard = hear.transcribe(clip, models.ASR)
            stress = hear.transcribe(clip, models.STRESS)
            value = check_audio.score(text, heard, stress)
            scored.append((value, text, clip, seconds(clip), heard))
            print("  %.2f   %-24s %5.2f  %s%s"
                  % (value, text, seconds(clip), heard, "   <- ships today" if i == 0 else ""))
        if not scored:
            continue
        scored.sort(reverse=True)
        best = scored[0]
        if best[1] != options[0]:
            winners[key] = (best[1], best[2])
            print("  -> %s" % best[1])
        else:
            print("  -> no candidate beat what ships")

    if not winners:
        print("\nnothing to publish")
        return

    manifest_path = os.path.join(HERE, "variants", "manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    entry = manifest.setdefault(VARIANT, {
        "id": VARIANT, "label": "respelled by the checker", "engine": "azure",
        "voice": "uk-UA-PolinaNeural", "texts": {},
    })
    for key, (text, clip) in winners.items():
        dest = os.path.join(OUT, key + ".ogg")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(clip, "rb") as src, open(dest, "wb") as out:
            out.write(src.read())
        entry["texts"][key] = text
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\n%d rows published to the %s column" % (len(winners), VARIANT))


if __name__ == "__main__":
    main()
