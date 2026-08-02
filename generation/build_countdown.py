# Build the Midnight-style combined countdown files from the per-number oggs.
#
# DBM 12.x stopped playing count/5.ogg .. count/1.ogg one by one; it plays a single
# pre-assembled file instead (DBM-Core/modules/objects/BossMod.lua). The layout is
# copied from DBM-Core/Sounds/Corsica:
#   fivecount.ogg     5.000 s  - numbers start at 0,1,2,3,4 s
#   threecount.ogg    5.000 s  - 2 s of silence, then 3,2,1 at 2,3,4 s
#   fivecount_5s.ogg  10.000 s - 5 s of silence, then the fivecount layout
#   threecount_5s.ogg 10.000 s - 7 s of silence, then 3,2,1 at 7,8,9 s
# The _5s variants are used when the timer highlight window is 10 s.
import os, subprocess, sys

SP = os.path.dirname(os.path.abspath(__file__))
COUNT = os.path.join(os.path.dirname(SP), "count")
RATE = 44100

# (output, leading silence in seconds, numbers spoken in order)
LAYOUTS = [
    ("fivecount.ogg", 0, [5, 4, 3, 2, 1]),
    ("threecount.ogg", 2, [3, 2, 1]),
    ("fivecount_5s.ogg", 5, [5, 4, 3, 2, 1]),
    ("threecount_5s.ogg", 7, [3, 2, 1]),
]


def build(out, lead, numbers):
    inputs, filters, labels = [], [], []
    if lead:
        inputs += ["-f", "lavfi", "-t", str(lead), "-i", f"anullsrc=r={RATE}:cl=mono"]
        labels.append("[0:a]")
    for i, n in enumerate(numbers):
        inputs += ["-i", os.path.join(COUNT, f"{n}.ogg")]
        idx = i + (1 if lead else 0)
        # one second per number: pad the clip with silence, then cut at exactly 1 s
        filters.append(
            f"[{idx}:a]aresample={RATE},aformat=sample_fmts=fltp:channel_layouts=mono,"
            f"apad,atrim=0:1,asetpts=N/SR/TB[n{i}]"
        )
        labels.append(f"[n{i}]")
    graph = ";".join(filters + ["".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph,
           "-map", "[out]", "-c:a", "libvorbis", "-q:a", "4", "-ar", str(RATE),
           os.path.join(COUNT, out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{out}: {r.stderr[:400]}")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", os.path.join(COUNT, out)],
                         capture_output=True, text=True).stdout.strip()
    print(f"{out:20} {float(dur):.3f} s")
    return float(dur)


if __name__ == "__main__":
    for out, lead, numbers in LAYOUTS:
        expected = 5.0 if "_5s" not in out else 10.0
        got = build(out, lead, numbers)
        assert abs(got - expected) < 0.05, f"{out}: expected {expected}s, got {got}s"
    print("countdown files OK")
