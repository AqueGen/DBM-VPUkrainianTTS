#!/usr/bin/env python3
"""Score bake-off columns on the same phrases so voices can be ranked before anyone listens.

Per variant, over the keys every scored variant has rendered:
  match   words heard vs words sent, the better of the two recognisers (check_audio.score);
          a foreign accent or a mangled word shows up here
  mos     UTMOS22 naturalness, 1-5, only with --mos (runs code fetched by torch.hub).
          Trained on English, so it ranks how synthetic a clip sounds, not how Ukrainian
  pitch   spread of the voice's pitch inside a clip, p90-p10 in semitones: flat vs lively
  hz      median pitch
  bright  spectral centroid in Hz
  rate    vowels per second of speech
  length  mean clip length in seconds

Run:  python generation/score_voices.py [--mos] [variant ...]   (default: every variant)
Writes generation/variants/scores.tsv.
"""
import json
import os
import sys

import numpy as np

import hear
import models
from bakeoff import table
from check_audio import score

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANTS = os.path.join(HERE, "variants")
REPORT = os.path.join(VARIANTS, "scores.tsv")
os.environ.setdefault("TORCH_HOME", os.path.join(models.CACHE, "torch"))

VOWELS = set("аеєиіїоуюяАЕЄИІЇОУЮЯ")
_MOS = []


def mos(wave):
    import torch
    if not _MOS:
        _MOS.append(torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True))
    with torch.no_grad():
        return float(_MOS[0](torch.from_numpy(wave.copy()).unsqueeze(0), sr=16000)[0])


def pitch(wave):
    import parselmouth
    track = parselmouth.Sound(wave.astype("float64"), 16000).to_pitch(pitch_floor=60, pitch_ceiling=500)
    f0 = track.selected_array["frequency"]
    f0 = f0[f0 > 0]
    if len(f0) < 5:
        return float("nan"), float("nan")
    semitones = 12 * np.log2(f0 / np.median(f0))
    return float(np.percentile(semitones, 90) - np.percentile(semitones, 10)), float(np.median(f0))


def brightness(wave):
    spectrum = np.abs(np.fft.rfft(wave * np.hanning(len(wave))))
    freqs = np.fft.rfftfreq(len(wave), 1 / 16000)
    return float((spectrum * freqs).sum() / spectrum.sum())


def measure(clip, sent, with_mos, written=None):
    """written: the words meant, when what was sent is IPA the recognisers cannot match."""
    sent = written if written and "/" in sent else sent
    wave = hear._audio(clip)
    seconds = len(wave) / 16000
    spread, hz = pitch(wave)
    heard, stress = hear.transcribe(clip, models.ASR), hear.transcribe(clip, models.STRESS)
    return {
        "heard": heard,
        "stress": stress,
        "match": score(sent, heard, stress),
        "mos": mos(wave) if with_mos else float("nan"),
        "pitch": spread,
        "hz": hz,
        "bright": brightness(wave),
        "rate": sum(c in VOWELS for c in sent) / seconds,
        "length": seconds,
    }


def main():
    manifest = json.load(open(os.path.join(VARIANTS, "manifest.json"), encoding="utf-8"))
    with_mos = "--mos" in sys.argv
    wanted = [a for a in sys.argv[1:] if a != "--mos"] or list(manifest)
    # A partial run must not overwrite the full per-clip report.
    report = REPORT if len(wanted) == len(manifest) else REPORT.replace(".tsv", "-subset.tsv")
    rendered = {v: {k for k in manifest[v]["texts"]
                    if os.path.isfile(os.path.join(VARIANTS, v, k + ".ogg"))} for v in wanted}
    keys = sorted(set.intersection(*rendered.values()))
    print("%d variants on %d shared keys" % (len(wanted), len(keys)))

    written = table()
    columns = ["match", "mos", "pitch", "hz", "bright", "rate", "length"]
    lines = ["variant\tkey\t" + "\t".join(columns) + "\tsent\theard\tstress"]
    summary = []
    for vid in wanted:
        rows = []
        for key in keys:
            row = measure(os.path.join(VARIANTS, vid, key + ".ogg"), manifest[vid]["texts"][key],
                          with_mos, written[key][1] if key in written else None)
            rows.append(row)
            lines.append("%s\t%s\t%s\t%s\t%s\t%s" % (
                vid, key, "\t".join("%.3f" % row[c] for c in columns),
                manifest[vid]["texts"][key], row["heard"], row["stress"]))
        means = {c: float(np.nanmean([r[c] for r in rows])) for c in columns}
        means["worst"] = min(r["match"] for r in rows)
        summary.append((vid, means))
        print("  %s" % vid, flush=True)

    with open(report, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    summary.sort(key=lambda item: -item[1]["mos" if with_mos else "match"])
    print("\n%-16s %6s %6s %5s %6s %6s %6s %6s %6s" % (
        "variant", "match", "worst", "mos", "pitch", "hz", "bright", "rate", "length"))
    for vid, m in summary:
        print("%-16s %6.2f %6.2f %5.2f %6.1f %6.0f %6.0f %6.1f %6.2f" % (
            vid, m["match"], m["worst"], m["mos"], m["pitch"], m["hz"], m["bright"], m["rate"], m["length"]))
    print("\nper clip: %s" % report)


if __name__ == "__main__":
    main()
