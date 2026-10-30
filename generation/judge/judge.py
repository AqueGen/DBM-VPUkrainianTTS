"""Ask Gemini (Vertex AI) to listen to a clip and judge it like a native Ukrainian listener.

judge(path, text) -> {"verdict": "pass"|"fail", "problems": [...]}
"""
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, r"G:\Games\World of Warcraft\_retail_\Interface\AddOns\DBM-VPUkrainianTTS\generation")
import bakeoff

import os

MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.1-pro-preview")
URL = ("https://aiplatform.googleapis.com/v1/projects/%s/locations/global/publishers/google/models/%s:generateContent"
       % (bakeoff.GOOGLE_PROJECT, MODEL))
PROMPT = """You are a strict native Ukrainian listener reviewing a voice line for a World of Warcraft boss-warning addon.
The line must say exactly: "{text}"{note}
Listen to the audio and fail it if ANY of these is true:
- a sound is missing, added or replaced (e.g. a dropped "в", an extra syllable at the end, "о" said as "а")
- a word has the wrong stress for standard Ukrainian
- Russian-sounding pronunciation (e.g. "вперьод" instead of "вперед", akanye)
- a short function word (на, в, у, до) is stressed or emphasised as if it were the key word
- the line is drawn out, sluggish, has unnatural pauses, or an acronym is read slowly letter by letter
- intonation or rhythm sounds unnatural for a short, urgent in-game callout
Pass it only if a native listener would accept it as is.
Answer JSON: {{"verdict": "pass" or "fail", "problems": ["short description", ...]}}"""
_TOKEN = []


def token():
    if not _TOKEN:
        _TOKEN.append(subprocess.run([bakeoff.GCLOUD, "auth", "application-default", "print-access-token"],
                                     capture_output=True, text=True, check=True).stdout.strip())
    return _TOKEN[0]


def judge(path, text, note=""):
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": PROMPT.format(text=text, note=("\n" + note) if note else "")},
            {"inlineData": {"mimeType": "audio/ogg", "data": base64.b64encode(open(path, "rb").read()).decode()}},
        ]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), headers={
        "Authorization": "Bearer " + token(), "x-goog-user-project": bakeoff.GOOGLE_PROJECT,
        "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.load(r)
            return json.loads(out["candidates"][0]["content"]["parts"][-1]["text"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503):
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError("%d %s" % (e.code, e.read()[:300].decode("utf-8", "replace")))
        except (TimeoutError, OSError, KeyError, ValueError):  # read timeout, reset, empty or non-JSON answer
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("gave up")
