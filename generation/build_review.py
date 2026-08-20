#!/usr/bin/env python3
"""Build a local review page (generation/review.html) listing every voice-pack phrase
with its English source line, the Ukrainian line, and play buttons for both this pack
and the reference English pack (DBM-VPVEM).

Run:  python generation/build_review.py
Then open generation/review.html in a browser.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.dirname(HERE)                      # DBM-VPUkrainianTTS
ADDONS = os.path.dirname(PACK)
REF = os.path.join(ADDONS, "DBM-VPVEM")           # English reference pack
SOUND_KEYS = os.path.join(ADDONS, "DBM-Core", "VoicePackSounds.lua")


def dbm_keys():
    """Every sound key current DBM-Core knows about, so new ones show up as missing."""
    try:
        with open(SOUND_KEYS, encoding="utf-8") as fh:
            return re.findall(r'^\s*\["([^"]+)"\]', fh.read(), re.M)
    except OSError:
        return []


def read_table(name):
    rows = []
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[0].strip():
                rows.append(parts[:3])
    return rows


def category(key):
    return key.split("/", 1)[0] if "/" in key else "core"


def build():
    rows = []
    for key, en, ua in read_table("ua_table.tsv") + read_table("events_table.tsv"):
        rows.append({
            "key": key,
            "en": en,
            "ua": ua,
            "cat": category(key),
            "hasUa": os.path.isfile(os.path.join(PACK, key + ".ogg")),
            "hasEn": os.path.isfile(os.path.join(REF, key + ".ogg")),
        })
    known = {r["key"] for r in rows}
    for key in sorted(set(dbm_keys()) - known):
        rows.append({
            "key": key,
            "en": "(new DBM key, no english line yet)",
            "ua": "",
            "cat": "missing",
            "hasUa": False,
            "hasEn": os.path.isfile(os.path.join(REF, key + ".ogg")),
        })
    rows.sort(key=lambda r: (r["cat"] != "core", r["cat"], r["key"]))

    # Escape "<" so a phrase containing "</script>" cannot close the inline script block.
    data = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    out = os.path.join(HERE, "review.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE.replace("__DATA__", data))
    print("wrote %s (%d phrases)" % (out, len(rows)))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<title>DBM-VPUkrainianTTS - phrase review</title>
<style>
:root { color-scheme: dark; }
body { margin: 0; font: 14px/1.4 "Segoe UI", system-ui, sans-serif; background: #14161a; color: #e6e6e6; }
header { position: sticky; top: 0; z-index: 2; background: #1b1e24; border-bottom: 1px solid #2c313a; padding: 10px 16px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
h1 { font-size: 15px; margin: 0 12px 0 0; color: #ffd100; font-weight: 600; }
input[type=search], select { background: #24282f; border: 1px solid #3a404a; color: #e6e6e6; padding: 6px 8px; border-radius: 4px; }
input[type=search] { min-width: 260px; }
label.chk { display: flex; align-items: center; gap: 5px; cursor: pointer; }
button { background: #2b313a; border: 1px solid #3d4552; color: #e6e6e6; border-radius: 4px; padding: 4px 10px; cursor: pointer; }
button:hover:not(:disabled) { background: #39424f; }
button:disabled { opacity: .3; cursor: default; }
button.playing { background: #4a6b2f; border-color: #6d9a45; }
#stats { margin-left: auto; color: #8b93a0; font-size: 12px; }
table { border-collapse: collapse; width: 100%; }
th { position: sticky; top: 51px; background: #1b1e24; text-align: left; padding: 6px 10px; font-size: 12px; color: #8b93a0; border-bottom: 1px solid #2c313a; z-index: 1; }
td { padding: 4px 10px; border-bottom: 1px solid #23272e; vertical-align: middle; }
tr:hover td { background: #1c2027; }
tr.flagged td { background: #3a2418; }
tr.flagged:hover td { background: #462b1c; }
.key { color: #7fa8d6; font-family: Consolas, monospace; font-size: 12px; }
.ua { color: #ffd100; }
.missing { color: #d66; font-style: italic; }
td.act { width: 1%; white-space: nowrap; }
#export { display: none; width: 100%; height: 160px; background: #0f1114; color: #cfd6e0; border: 0; border-top: 1px solid #2c313a; font-family: Consolas, monospace; font-size: 12px; padding: 10px; box-sizing: border-box; }
</style>
</head>
<body>
<header>
  <h1>DBM-VPUkrainianTTS</h1>
  <input type="search" id="q" placeholder="filter: key / english / ukrainian">
  <select id="cat"></select>
  <label class="chk"><input type="checkbox" id="onlyFlagged"> only flagged</label>
  <button id="showExport">export flagged</button>
  <span id="stats"></span>
</header>
<table>
  <thead><tr><th>key</th><th>english</th><th>ukrainian</th><th>play</th><th>flag</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<textarea id="export" readonly></textarea>
<script>
const DATA = __DATA__;
const FLAG_KEY = "vpua-flagged";
const flagged = new Set(JSON.parse(localStorage.getItem(FLAG_KEY) || "[]"));
const player = new Audio();
let current = null;

function saveFlags() { localStorage.setItem(FLAG_KEY, JSON.stringify([...flagged])); }

function play(btn, src) {
  if (current === btn && !player.paused) { player.pause(); return; }
  if (current) current.classList.remove("playing");
  current = btn;
  btn.classList.add("playing");
  player.src = src;
  player.play().catch(function (e) {
    btn.classList.remove("playing");
    alert("cannot play " + src + "\n" + e);
  });
}
player.addEventListener("ended", function () { if (current) current.classList.remove("playing"); });
player.addEventListener("pause", function () { if (current) current.classList.remove("playing"); });

function makeBtn(label, src, enabled) {
  const b = document.createElement("button");
  b.textContent = label;
  b.disabled = !enabled;
  if (enabled) b.onclick = function () { play(b, src); };
  return b;
}

const tbody = document.getElementById("rows");
const rowEls = DATA.map(function (d) {
  const tr = document.createElement("tr");
  if (flagged.has(d.key)) tr.classList.add("flagged");

  const tdKey = document.createElement("td");
  tdKey.className = "key";
  tdKey.textContent = d.key;

  const tdEn = document.createElement("td");
  tdEn.textContent = d.en;

  const tdUa = document.createElement("td");
  tdUa.className = d.ua ? "ua" : "missing";
  tdUa.textContent = d.ua || "(not recorded)";

  const tdAct = document.createElement("td");
  tdAct.className = "act";
  tdAct.append(makeBtn("EN", "../../DBM-VPVEM/" + d.key + ".ogg", d.hasEn), " ",
               makeBtn("UA", "../" + d.key + ".ogg", d.hasUa));

  const tdFlag = document.createElement("td");
  tdFlag.className = "act";
  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.checked = flagged.has(d.key);
  cb.onchange = function () {
    if (cb.checked) { flagged.add(d.key); } else { flagged.delete(d.key); }
    tr.classList.toggle("flagged", cb.checked);
    saveFlags();
    render();
  };
  tdFlag.append(cb);

  tr.append(tdKey, tdEn, tdUa, tdAct, tdFlag);
  tbody.append(tr);
  return { d: d, tr: tr };
});

const sel = document.getElementById("cat");
sel.append(new Option("all categories", ""));
[...new Set(DATA.map(function (d) { return d.cat; }))].forEach(function (c) {
  sel.append(new Option(c, c));
});

const q = document.getElementById("q");
const onlyFlagged = document.getElementById("onlyFlagged");

function render() {
  const needle = q.value.trim().toLowerCase();
  const cat = sel.value;
  let shown = 0;
  for (const row of rowEls) {
    const d = row.d;
    const hit = !needle || (d.key + " " + d.en + " " + d.ua).toLowerCase().includes(needle);
    const ok = hit && (!cat || d.cat === cat) && (!onlyFlagged.checked || flagged.has(d.key));
    row.tr.style.display = ok ? "" : "none";
    if (ok) shown++;
  }
  document.getElementById("stats").textContent =
    shown + " / " + DATA.length + " shown - " + flagged.size + " flagged";
}

q.oninput = sel.onchange = onlyFlagged.onchange = render;

const exportBox = document.getElementById("export");
document.getElementById("showExport").onclick = function () {
  const lines = DATA.filter(function (d) { return flagged.has(d.key); })
                    .map(function (d) { return [d.key, d.en, d.ua].join("\t"); });
  if (!lines.length) { alert("nothing flagged yet"); return; }
  exportBox.value = lines.join("\n");
  exportBox.style.display = "block";
  exportBox.focus();
  exportBox.select();
};

render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
