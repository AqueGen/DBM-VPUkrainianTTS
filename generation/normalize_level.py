#!/usr/bin/env python3
"""Bring every clip to the same level.

A neural voice varies with what it is saying: across this pack the mean level spreads
about 5 dB, which in game is heard as one warning shouting and the next mumbling. Each
clip gets a fixed gain toward the pack's median - a plain volume change, not compression,
so nothing about the delivery is altered.

Run:  python generation/normalize_level.py [target_dB]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)
TOLERANCE = 0.3  # leave a clip alone if it is already this close


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


def level(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True)
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", out.stderr)
    peak = re.search(r"max_volume: (-?[\d.]+) dB", out.stderr)
    return (float(mean.group(1)) if mean else None,
            float(peak.group(1)) if peak else None)


def apply_gain(path, gain_db):
    tmp = path + ".gain.ogg"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                        "-af", "volume=%.2fdB" % gain_db,
                        "-c:a", "libvorbis", "-q:a", "4", "-ar", "44100", tmp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL %s: %s" % (path, r.stderr[:160]))
        if os.path.exists(tmp):
            os.remove(tmp)
        return False
    os.replace(tmp, path)
    return True


def main():
    measured = []
    for path in clips():
        mean, peak = level(path)
        if mean is not None:
            measured.append((mean, peak, path))
    if not measured:
        raise SystemExit("no clips found")

    measured.sort()
    target = float(sys.argv[1]) if len(sys.argv) > 1 else measured[len(measured) // 2][0]
    print("%d clips, current spread %.1f to %.1f dB, target %.1f"
          % (len(measured), measured[0][0], measured[-1][0], target))

    changed = clipped = 0
    for mean, peak, path in measured:
        gain = target - mean
        if abs(gain) < TOLERANCE:
            continue
        # Never push a clip into clipping: keep at least a little headroom on the peak.
        if peak is not None and peak + gain > -1.0:
            gain = -1.0 - peak
            clipped += 1
        if abs(gain) >= TOLERANCE and apply_gain(path, gain):
            changed += 1

    after = sorted(level(p)[0] for _, _, p in measured)
    print("adjusted %d clips (%d limited by headroom), new spread %.1f to %.1f dB"
          % (changed, clipped, after[0], after[-1]))


if __name__ == "__main__":
    main()
