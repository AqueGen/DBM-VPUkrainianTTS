#!/usr/bin/env python3
"""Watch DBM for voice keys we do not speak yet, and for a raised pack version floor.

check_pack.py compares the pack against our own table, so it can never notice that DBM
started asking for a sound we never recorded: that key is simply silent in a fight.
This reads DBM's own registry instead.

Run:  python generation/check_dbm_keys.py
      python generation/check_dbm_keys.py --local "<path to DBM-Core>"
"""
import argparse
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)
TOC = os.path.join(PACK, "DBM-VPUkrainianTTS_Mainline.toc")

RAW = "https://raw.githubusercontent.com/DeadlyBossMods/DBM-Retail/master/"
SOUNDS = "DBM-Core/VoicePackSounds.lua"
VERSIONS = "DBM-Core/modules/objects/VoicePacks.lua"


def read(relative, local):
    if local:
        with open(os.path.join(local, relative.split("/", 1)[1]), encoding="utf-8") as fh:
            return fh.read()
    with urllib.request.urlopen(RAW + relative, timeout=30) as response:
        return response.read().decode("utf-8")


def dbm_keys(text):
    return {found.group(1) for found in re.finditer(r'^\s*\["([^"]+)"\]\s*=', text, re.M)}


def dbm_minimum(text):
    found = re.search(r"local minVoicePackVersion\s*=\s*(\d+)", text)
    return int(found.group(1)) if found else None


def our_keys():
    keys = set()
    with open(os.path.join(HERE, "ua_table.tsv"), encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0].strip():
                keys.add(parts[0].strip())
    return keys


def our_version():
    with open(TOC, encoding="utf-8") as fh:
        found = re.search(r"^## X-DBM-Voice-Version:\s*(\d+)", fh.read(), re.M)
    return int(found.group(1)) if found else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", help="read DBM's files from a DBM-Core folder instead of GitHub")
    args = parser.parse_args()

    sounds = read(SOUNDS, args.local)
    versions = read(VERSIONS, args.local)

    theirs, ours = dbm_keys(sounds), our_keys()
    minimum, version = dbm_minimum(versions), our_version()

    problems = []
    unspoken = sorted(theirs - ours)
    if unspoken:
        problems.append("%d keys DBM knows and the pack does not speak:\n    %s"
                        % (len(unspoken), "\n    ".join(unspoken)))
    if minimum is None or version is None:
        problems.append("could not read a version: DBM minimum %s, pack %s" % (minimum, version))
    elif version < minimum:
        problems.append("DBM now wants voice pack version %d, the pack declares %d - "
                        "players get the outdated warning and lose the newer lines"
                        % (minimum, version))

    retired = sorted(ours - theirs)
    print("DBM registry: %d keys, minimum pack version %s" % (len(theirs), minimum))
    print("This pack: %d keys, version %s" % (len(ours), version))
    if retired:
        print("%d keys the pack speaks and DBM no longer lists (harmless): %s"
              % (len(retired), ", ".join(retired[:8])))
    if problems:
        print("")
        for line in problems:
            print("  " + line)
        return 1
    print("nothing new to record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
