#!/usr/bin/env python3
"""Trim dead air from already-rendered clips.

New renders are trimmed as they are written (see bakeoff.to_ogg); this catches the ones
made before that, so a comparison by ear is not distorted by silence one engine adds and
another does not.

Run:  python generation/trim_silence.py variants/azure-polina variants/polina-all
"""
import os
import subprocess
import sys

import bakeoff

HERE = os.path.dirname(os.path.abspath(__file__))


def clips(folder):
    for root, _, files in os.walk(folder):
        for name in files:
            if name.endswith(".ogg"):
                yield os.path.join(root, name)


def seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def main():
    targets = sys.argv[1:] or ["variants"]
    for target in targets:
        folder = target if os.path.isabs(target) else os.path.join(HERE, target)
        before = after = 0.0
        count = 0
        for path in clips(folder):
            was = seconds(path)
            tmp = path + ".trim.ogg"
            if not bakeoff.to_ogg(path, tmp):
                continue
            now = seconds(tmp)
            # A clip that is all quiet would trim to nothing; keep the original instead.
            if now < 0.15:
                os.remove(tmp)
                print("kept (too quiet to trim): %s" % path)
                continue
            os.replace(tmp, path)
            before += was
            after += now
            count += 1
        if count:
            print("%s: %d clips, %.1f s -> %.1f s (-%.0f%%)"
                  % (target, count, before, after, 100 * (1 - after / before)))


if __name__ == "__main__":
    main()
