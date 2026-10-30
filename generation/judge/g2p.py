"""Expected phones for Ukrainian text via the bundled espeak-ng (uk voice)."""
import sys

import espeakng_loader
from phonemizer.backend import EspeakBackend
from phonemizer.backend.espeak.wrapper import EspeakWrapper
from phonemizer.separator import Separator

EspeakWrapper.set_library(espeakng_loader.get_library_path())
EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
_BACKEND = []


def phones(text):
    if not _BACKEND:
        _BACKEND.append(EspeakBackend("uk", preserve_punctuation=False, with_stress=True))
    out = _BACKEND[0].phonemize([text], separator=Separator(phone=" ", word=" | "), strip=True)[0]
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for t in sys.argv[1:]:
        print(t, "->", phones(t))
