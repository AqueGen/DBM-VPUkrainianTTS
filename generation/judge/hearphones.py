"""Phones heard in a clip by facebook/wav2vec2-xlsr-53-espeak-cv-ft (espeak-style IPA)."""
import os
import sys

GEN = r"G:\Games\World of Warcraft\_retail_\Interface\AddOns\DBM-VPUkrainianTTS\generation"
sys.path.insert(0, GEN)
import g2p  # noqa: F401  (points phonemizer at the bundled espeak before the tokenizer loads)
import hear
import models

REPO = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
_M = []


def heard(path):
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    if not _M:
        p = Wav2Vec2Processor.from_pretrained(REPO, cache_dir=models.CACHE)
        m = Wav2Vec2ForCTC.from_pretrained(REPO, cache_dir=models.CACHE).eval()
        _M.extend([p, m])
    p, m = _M
    inputs = p(hear._audio(path), sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        ids = m(**inputs).logits.argmax(-1)
    return p.batch_decode(ids)[0].strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for a in sys.argv[1:]:
        print(os.path.basename(os.path.dirname(a)), os.path.basename(a), "->", heard(a))
