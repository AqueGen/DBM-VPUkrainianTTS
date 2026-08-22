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
import subprocess

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


def duration(path):
    """Seconds of audio, or None. Length is half the argument when wording is compared."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", path], capture_output=True, text=True)
        return round(float(out.stdout.strip()), 2)
    except (OSError, ValueError):
        return None


def load_variants():
    """Bake-off renderings written by bakeoff.py, one column per variant, oldest first."""
    manifest = os.path.join(HERE, "variants", "manifest.json")
    try:
        with open(manifest, encoding="utf-8") as fh:
            raw = json.load(fh)
    except OSError:
        return []
    out = []
    for vid, entry in raw.items():
        texts, secs = {}, {}
        for key, text in entry.get("texts", {}).items():
            ogg = os.path.join(HERE, "variants", vid, key + ".ogg")
            if os.path.isfile(ogg):
                texts[key] = text
                secs[key] = duration(ogg)
        if texts:
            out.append({"id": vid, "label": entry.get("label", vid),
                        "texts": texts, "secs": secs})
    return out


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
    variants = load_variants()
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
    def embed(value):
        return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")

    out = os.path.join(HERE, "review.html")
    page = TEMPLATE.replace("__DATA__", embed(rows)).replace("__VARIANTS__", embed(variants))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote %s (%d phrases, %d bake-off variants)" % (out, len(rows), len(variants)))


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
/* Every round adds a column, so this table outgrows the window: scroll it on its own
   and pin the key so a row stays identifiable however far right you get. */
#bake { padding: 12px 16px 4px; border-bottom: 2px solid #2c313a; overflow-x: auto; }
#bake th:first-child, #bake td:first-child { position: sticky; left: 0; background: #14161a; z-index: 2; }
#bake tr:hover td:first-child { background: #1c2027; }
#bake h2 { font-size: 13px; color: #8b93a0; margin: 0 0 8px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
#bake table { table-layout: auto; }
#bake th { position: static; }
#bake td { vertical-align: top; }
#bake .sent { display: block; margin-top: 3px; color: #9aa4b2; font-family: Consolas, monospace; font-size: 11px; max-width: 220px; }
#bake .sent.changed { color: #ffd100; }
#bake .pick { margin-right: 5px; }
#bake .secs { margin-left: 6px; color: #6f7885; font-size: 11px; font-family: Consolas, monospace; }
#bake .none { color: #555c67; }
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
<section id="bake"></section>
<table>
  <thead><tr><th>key</th><th>english</th><th>ukrainian</th><th>play</th><th>flag</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<textarea id="export" readonly></textarea>
<script>
const DATA = __DATA__;
const VARIANTS = __VARIANTS__;
const FLAG_KEY = "vpua-flagged";
const PICK_KEY = "vpua-picks";
const flagged = new Set(JSON.parse(localStorage.getItem(FLAG_KEY) || "[]"));
const picks = JSON.parse(localStorage.getItem(PICK_KEY) || "{}");
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
    alert("cannot play " + src + "\n" + e +
          "\n\nThe file exists but did not load - the local server is usually gone." +
          "\nRestart it with: python generation/serve.py");
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

// Bake-off: one column per rendering, plus a radio to record which one wins.
function buildBakeoff() {
  const host = document.getElementById("bake");
  if (!VARIANTS.length) { host.remove(); return; }
  const keys = [...new Set(VARIANTS.flatMap(function (v) { return Object.keys(v.texts); }))];
  const byKey = {};
  DATA.forEach(function (d) { byKey[d.key] = d; });

  const head = document.createElement("h2");
  head.textContent = "bake-off";
  const exportPicks = document.createElement("button");
  exportPicks.textContent = "export picks";
  exportPicks.style.marginLeft = "10px";
  exportPicks.onclick = function () {
    const lines = keys.filter(function (k) { return picks[k]; })
                      .map(function (k) { return k + "\t" + picks[k]; });
    if (!lines.length) { alert("nothing picked yet"); return; }
    const box = document.getElementById("export");
    box.value = lines.join("\n");
    box.style.display = "block";
    box.focus();
    box.select();
  };
  head.append(exportPicks);
  host.append(head);

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  ["key", "english", "pack (current)"].concat(VARIANTS.map(function (v) { return v.label; }))
    .forEach(function (t) {
      const th = document.createElement("th");
      th.textContent = t;
      hr.append(th);
    });
  thead.append(hr);
  table.append(thead);

  const body = document.createElement("tbody");
  keys.forEach(function (key) {
    const d = byKey[key] || { en: "", ua: "" };
    const tr = document.createElement("tr");

    const tdKey = document.createElement("td");
    tdKey.className = "key";
    tdKey.textContent = key;

    const tdEn = document.createElement("td");
    tdEn.textContent = d.en;

    const tdPack = document.createElement("td");
    tdPack.append(makeBtn("play", "../" + key + ".ogg", !!d.hasUa));
    const orig = document.createElement("span");
    orig.className = "sent";
    orig.textContent = d.ua;
    tdPack.append(orig);

    tr.append(tdKey, tdEn, tdPack);

    VARIANTS.forEach(function (v) {
      const td = document.createElement("td");
      const sent = v.texts[key];
      if (!sent) {
        td.className = "none";
        td.textContent = "-";
        tr.append(td);
        return;
      }
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.className = "pick";
      radio.name = "pick-" + key;
      radio.checked = picks[key] === v.id;
      radio.onchange = function () {
        picks[key] = v.id;
        localStorage.setItem(PICK_KEY, JSON.stringify(picks));
      };
      td.append(radio, makeBtn("play", "variants/" + v.id + "/" + key + ".ogg", true));
      const secs = v.secs && v.secs[key];
      if (secs) {
        const s = document.createElement("span");
        s.className = "secs";
        s.textContent = secs.toFixed(2) + "s";
        td.append(s);
      }
      const txt = document.createElement("span");
      txt.className = "sent" + (sent !== d.ua ? " changed" : "");
      txt.textContent = sent;
      td.append(txt);
      tr.append(td);
    });
    body.append(tr);
  });
  table.append(body);
  host.append(table);
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

buildBakeoff();
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
