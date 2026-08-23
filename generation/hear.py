#!/usr/bin/env python3
"""Ask a machine where the stress landed and what the words were.

Two local models, no API and no listening:
  * Yehor/w2v-bert-uk-v2.1                - what was said
  * mouseyy/uk_wav2vec2_with_stress_mark  - where the stress fell, marked with "+"

Whether the stress model follows the audio or just recites a dictionary is the open
question; this is the tool that lets it be answered on real clips.

Run:  python generation/hear.py clip.ogg [clip2.ogg ...]
"""
import os
import sys
import warnings

import models

warnings.filterwarnings("ignore")
os.environ.setdefault("HF_HOME", models.CACHE)

_LOADED = {}


def _pipeline(repo):
    if repo not in _LOADED:
        import torch
        from transformers import AutoModelForCTC, AutoProcessor
        processor = AutoProcessor.from_pretrained(repo, cache_dir=models.CACHE)
        model = AutoModelForCTC.from_pretrained(repo, cache_dir=models.CACHE)
        model.eval()
        _LOADED[repo] = (processor, model, torch)
    return _LOADED[repo]


def _audio(path, rate=16000):
    """Decode to mono float32 at the model's sample rate via ffmpeg."""
    import subprocess

    import numpy as np
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(rate), "-"],
        capture_output=True)
    return np.frombuffer(out.stdout, dtype="float32")


def transcribe(path, repo):
    processor, model, torch = _pipeline(repo)
    inputs = processor(_audio(path), sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    ids = logits.argmax(dim=-1)
    return processor.batch_decode(ids)[0].strip()


def main():
    paths = sys.argv[1:]
    if not paths:
        raise SystemExit(__doc__)
    print("%-34s %-28s %s" % ("file", "heard", "stress"))
    for path in paths:
        heard = transcribe(path, models.ASR)
        stress = transcribe(path, models.STRESS)
        print("%-34s %-28s %s" % (os.path.basename(path), heard, stress))


if __name__ == "__main__":
    main()
