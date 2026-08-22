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

# Spoken-language identification. Cheap triage: does a Ukrainian line come back as
# Ukrainian, or as Russian?
LANGID = "speechbrain/lang-id-voxlingua107-ecapa"

REPOS = [ASR, STRESS, LANGID]
# Not "*.ckpt": speechbrain ships its weights in that format.
IGNORE = ["*.h5", "*.msgpack", "*.tflite"]

# Piper voices trained on Ukrainian speech, for the free local side of the voice
# comparison. Matilda is an American-accent source voice and ElevenLabs says that accent
# leaks into multilingual output, so a natively Ukrainian voice is worth hearing.
PIPER_REPO = "rhasspy/piper-voices"
PIPER_VOICES = {
    "tetiana": "uk/uk_UA/tetiana/high/uk_UA-tetiana-high.onnx",
    "lada": "uk/uk_UA/lada/x_low/uk_UA-lada-x_low.onnx",
    "ukrainian_tts": "uk/uk_UA/ukrainian_tts/medium/uk_UA-ukrainian_tts-medium.onnx",
}


def piper_voice(name):
    """Local path of a Piper voice, downloading it (and its config) on first use."""
    from huggingface_hub import hf_hub_download
    onnx = PIPER_VOICES[name]
    path = hf_hub_download(repo_id=PIPER_REPO, filename=onnx, cache_dir=CACHE)
    hf_hub_download(repo_id=PIPER_REPO, filename=onnx + ".json", cache_dir=CACHE)
    return path


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
    for name in PIPER_VOICES:
        print("fetching piper voice %s ..." % name, flush=True)
        path = piper_voice(name)
        print("  %s  %.0f MB" % (path, os.path.getsize(path) / 1e6), flush=True)


if __name__ == "__main__":
    main()
