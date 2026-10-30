"""Judge vs the owner's own verdicts from this session."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8")
from judge import judge

V = r"G:\Games\World of Warcraft\_retail_\Interface\AddOns\DBM-VPUkrainianTTS\generation\variants"
S = os.path.dirname(HERE)
DPS = 'Note: "DPS" is meant as the English acronym (dee-pee-ess), spoken quickly as one unit.'
# (label, owner's verdict, clip, text, note)
CASES = [
    ("spear take 1 (spyska)", "fail", os.path.join(V, "el4-m-alex-spear-seed1", "spear.ogg"), "Спис", ""),
    ("spear take 2 (spyska)", "fail", os.path.join(V, "el4-m-alex-spear-seed2", "spear.ogg"), "Спис", ""),
    ("go plain (vperiod)", "fail", os.path.join(V, "el4-m-alex-go-plain", "com_go.ogg"), "Вперед, вперед, вперед!", ""),
    ("go u- (uperedd)", "fail", os.path.join(V, "el4-m-alex-go-u", "com_go.ogg"), "Вперед, вперед, вперед!", ""),
    ("go ipa v (uperedd)", "fail", os.path.join(V, "el4-m-alex-go-ipa-v", "com_go.ogg"), "Вперед, вперед, вперед!", ""),
    ("slower DPS pack", "fail", os.path.join(V, "el4-m-alex-all", "dpsslow.ogg"), "Повільніше DPS", DPS),
    ("slower DPS new take", "fail", os.path.join(HERE, "takes", "dpsslow", "97c76ffbdf-s1.ogg"), "Повільніше DPS", DPS),
    ("slower DPS tight x1.15", "fail", os.path.join(S, "tight", "x1.15", "dpsslow.ogg"), "Повільніше DPS", DPS),
    ("slower DPS splice A", "fail", os.path.join(S, "splice", "tight", "dpsslow-a.ogg"), "Повільніше DPS", DPS),
    ("slower DPS splice B", "fail", os.path.join(S, "splice", "tight", "dpsslow-b.ogg"), "Повільніше DPS", DPS),
    ("more DPS pack", "pass", os.path.join(V, "el4-m-alex-dps-latin", "dpsmore.ogg"), "Більше DPS", DPS),
] + [("na tobi IPA %s" % k, "pass", os.path.join(V, "el4-m-alex-na-ipa", k + ".ogg"), t, "")
     for k, t in (("lineyou", "Лінія на тобі"), ("coinyou", "Монета на тобі"), ("greenyou", "Зелений на тобі"),
                  ("arrowyou", "Стріла на тобі"), ("absorbyou", "Поглинання на тобі"))]

agree = 0
for label, owner, clip, text, note in CASES:
    r = judge(clip, text, note)
    ok = r.get("verdict") == owner
    agree += ok
    print("%s %-26s owner %-4s judge %-4s %s" % ("OK " if ok else "XX ", label, owner, r.get("verdict"),
                                                  "; ".join(r.get("problems", []))), flush=True)
print("agree %d/%d" % (agree, len(CASES)))
