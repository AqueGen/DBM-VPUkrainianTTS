#!/usr/bin/env python3
"""Bring every clip to the loudness of the English DBM pack.

A neural voice varies with what it is saying, and it comes out of Azure near -20 LUFS,
while DBM-VPVEM sits near -13. Each clip gets the gain that lands it on the target,
with a limiter catching the peaks that gain pushes over the ceiling.

Run:  python generation/normalize_level.py [target_LUFS]
"""
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
# DBM_VP_PACK points at another voice's addon folder; the default is this one.
PACK = os.environ.get("DBM_VP_PACK") or os.path.dirname(HERE)
TARGET = -13.0
TOLERANCE = 0.3  # leave a clip alone if it is already this close
LIMIT = 10 ** (-1.5 / 20)


# The assembled countdowns are mostly silence by design, so their mean level says
# nothing about how loud the spoken numbers are. Normalising them would push the digits
# above everything else. They are rebuilt from the normalised digits instead.
ASSEMBLED = {"fivecount.ogg", "threecount.ogg", "fivecount_5s.ogg", "threecount_5s.ogg"}


def clips():
    for root, dirs, files in os.walk(PACK):
        dirs[:] = [d for d in dirs if d not in (".git", ".github", "generation", "docs", "assets")]
        for name in files:
            if name.endswith(".ogg") and name not in ASSEMBLED:
                yield os.path.join(root, name)


def loudness(path):
    # Looped, because R128 measures in 400 ms blocks and reads a shorter clip (count/3) as silence.
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-stream_loop", "3", "-i", path,
                          "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    level = float(found[-1]) if found else None
    return level if level is not None and level > -60 else None


def normalise(path, target):
    level = loudness(path)
    if level is None:
        print("SKIP %s: no measurable speech" % path)
        return None
    if abs(target - level) < TOLERANCE:
        return level
    src, tmp = path + ".src.ogg", path + ".gain.ogg"
    shutil.copyfile(path, src)
    # The limiter and the encoder each take back part of the gain, so it is tuned on the finished file.
    gain = target - level
    try:
        for _ in range(6):
            af = "volume=%.2fdB,alimiter=limit=%.4f:level=0:latency=1" % (gain, LIMIT)
            r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af,
                                "-c:a", "libvorbis", "-q:a", "4", "-ar", "44100", tmp],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print("FAIL %s: %s" % (path, r.stderr[:160]))
                return None
            level = loudness(tmp)
            if level is None or abs(target - level) < 0.2:
                break
            gain += target - level
        os.replace(tmp, path)
        return level
    finally:
        for leftover in (src, tmp):
            if os.path.exists(leftover):
                os.remove(leftover)


def main():
    target = float(sys.argv[1]) if len(sys.argv) > 1 else TARGET
    paths = list(clips())
    if not paths:
        raise SystemExit("no clips found")
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        after = sorted(v for v in pool.map(lambda p: normalise(p, target), paths) if v is not None)
    print("%d clips at target %.1f LUFS, now %.1f to %.1f, median %.1f"
          % (len(paths), target, after[0], after[-1], after[len(after) // 2]))


if __name__ == "__main__":
    main()
