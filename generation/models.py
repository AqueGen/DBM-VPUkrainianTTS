#!/usr/bin/env python3
"""Local model store for the pronunciation checks.

Weights live on F: rather than the system drive - the cache runs to several GB and C:
has far less room. Import CACHE from here instead of relying on the environment, so a
fresh shell or a scheduled run lands in the same place.

Run:  python generation/models.py          # download what is missing, report sizes
"""
import os

CACHE = os.environ.get("VPUA_MODEL_CACHE", r"F:\claude-data\hf-cache")
os.environ.setdefault("HF_HOME", CACHE)
# Creating a symlink on Windows needs a privilege this account does not hold, and the
# hub's own fallback still tries one (WinError 1314). Copy the blobs instead - the cache
# lives on a 3 TB drive, so the duplication does not matter.
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Ukrainian ASR, CTC over Ukrainian orthography. Used two ways: as a content check
# (did the take say the words?) and, because CTC exposes per-character posteriors, as the
# accent probe - Ukrainian и is [ɪ] and і is [i], so a Russian-coloured vowel moves the
# posterior mass between two letters the model was trained to tell apart.
ASR = "Yehor/w2v-bert-uk-v2.1"

# Emits "+" after the stressed vowel. Only useful if the mark follows the audio rather
# than a lexical prior - that is the experiment, not an assumption.
STRESS = "mouseyy/uk_wav2vec2_with_stress_mark"

REPOS = [ASR, STRESS]
IGNORE = ["*.h5", "*.msgpack", "*.tflite"]



def fetch(repo):
    from huggingface_hub import snapshot_download
    return snapshot_download(repo_id=repo, cache_dir=CACHE, ignore_patterns=IGNORE)


def size_of(path):
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def main():
    os.makedirs(CACHE, exist_ok=True)
    for repo in REPOS:
        print("fetching %s ..." % repo, flush=True)
        path = fetch(repo)
        print("  %s  %.0f MB" % (path, size_of(path) / 1e6), flush=True)


if __name__ == "__main__":
    main()
