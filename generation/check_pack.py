#!/usr/bin/env python3
"""Offline release gate: everything about the shipped files that can be checked for free.

No network, no models, no API. It answers the questions that would otherwise be found
by a player: is a sound missing, does a file fail to decode, is one clip twice as loud
as its neighbours, does a warning start late because of leading silence.

Run:  python generation/check_pack.py      (exit code 1 if anything fails)
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)

# Assembled by build_countdown.py rather than synthesised, and deliberately long.
ASSEMBLED = {"count/fivecount": 5.0, "count/threecount": 5.0,
             "count/fivecount_5s": 10.0, "count/threecount_5s": 10.0}

MAX_SECONDS = 4.5          # longest real phrase measured is Thogar/B2A4 at 4.27
MAX_LEAD_SILENCE = 0.15    # a late warning is the defect this pack exists to avoid
LOUDNESS_TOLERANCE = 1.5   # dB around the pack's own median


def keys_from_tables():
    keys = []
    for name in ("ua_table.tsv", "events_table.tsv"):
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3 and parts[0].strip():
                    keys.append(parts[0])
    return keys


def clips_on_disk():
    found = []
    for root, dirs, files in os.walk(PACK):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "generation", "docs", "assets")]
        for name in files:
            if name.endswith(".ogg"):
                rel = os.path.relpath(os.path.join(root, name), PACK)
                found.append(rel.replace(os.sep, "/")[:-4])
    return found


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_name,sample_rate,channels",
                          "-of", "json", path], capture_output=True, text=True)
    try:
        data = json.loads(out.stdout)
        stream = data["streams"][0]
        return (float(data["format"]["duration"]), stream["codec_name"],
                int(stream["sample_rate"]), int(stream["channels"]))
    except (ValueError, KeyError, IndexError):
        return None


def loudness(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True)
    m = re.search(r"mean_volume: (-?[\d.]+) dB", out.stderr)
    return float(m.group(1)) if m else None


def lead_silence(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af",
                          "silencedetect=noise=-45dB:d=0.05", "-f", "null", "-"],
                         capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", out.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out.stderr)]
    return ends[0] if (starts and ends and starts[0] <= 0.01) else 0.0


def main():
    problems = []
    keys = keys_from_tables()
    on_disk = set(clips_on_disk())

    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        problems.append("duplicate keys in the tables: %s" % ", ".join(sorted(duplicates)))
    missing = sorted(set(keys) - on_disk)
    if missing:
        problems.append("no audio for %d keys: %s" % (len(missing), ", ".join(missing[:8])))
    orphans = sorted(on_disk - set(keys) - set(ASSEMBLED))
    if orphans:
        problems.append("audio with no table row: %s" % ", ".join(orphans[:8]))

    levels = []
    for key in sorted(on_disk):
        path = os.path.join(PACK, key.replace("/", os.sep) + ".ogg")
        info = probe(path)
        if not info:
            problems.append("%s does not decode" % key)
            continue
        seconds, codec, rate, channels = info
        if codec != "vorbis":
            problems.append("%s is %s, not vorbis" % (key, codec))
        if rate != 44100:
            problems.append("%s is %d Hz, not 44100" % (key, rate))
        if channels != 1:
            problems.append("%s has %d channels" % (key, channels))
        if key in ASSEMBLED:
            if abs(seconds - ASSEMBLED[key]) > 0.05:
                problems.append("%s is %.2f s, expected %.1f" % (key, seconds, ASSEMBLED[key]))
            continue
        if seconds > MAX_SECONDS:
            problems.append("%s runs %.2f s, over the %.1f s cap" % (key, seconds, MAX_SECONDS))
        lead = lead_silence(path)
        if lead > MAX_LEAD_SILENCE:
            problems.append("%s starts %.2f s late" % (key, lead))
        level = loudness(path)
        if level is not None:
            levels.append((level, key))

    if levels:
        levels.sort()
        median = levels[len(levels) // 2][0]
        for level, key in levels:
            if abs(level - median) > LOUDNESS_TOLERANCE:
                problems.append("%s is %.1f dB against a median of %.1f" % (key, level, median))
        print("%d clips, median level %.1f dB" % (len(levels), median))

    print("%d keys in the tables, %d files on disk" % (len(keys), len(on_disk)))
    if problems:
        print("\n%d problems:" % len(problems))
        for line in problems[:40]:
            print("  " + line)
        return 1
    print("pack looks shippable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
