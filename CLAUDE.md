# DBM-VPUkrainianTTS

Ukrainian female TTS voice pack for Deadly Boss Mods, generated with Azure AI Speech (`uk-UA-PolinaNeural`).

The Azure resource must stay on the **Standard (S0)** tier. The free tier synthesises the same audio, but Microsoft's terms grant the right to use the output only on a paid tier - and this pack is published. S0 includes 500,000 characters of neural TTS per month at no cost against roughly 9,000 for a full regeneration, so the tier costs nothing and settles the licence.

## Release Process

Releases are driven by [release-please](https://github.com/googleapis/release-please) from **Conventional Commits**. Nothing is versioned by hand.

- Write commits as `feat: ...` (minor), `fix: ...` (patch), `feat!: ...` or a `BREAKING CHANGE:` footer (major). Anything else (`chore:`, `docs:`, `ci:`, `refactor:`) does not trigger a release on its own.
- On every push to `main`, `release-please.yml` opens or updates a **release PR** that bumps `## Version:` in `DBM-VPUkrainianTTS_Mainline.toc`, updates `CHANGELOG.md`, and updates `.release-please-manifest.json`.
- **Merging that PR** publishes everything: the `v<semver>` tag, the GitHub release, and the CurseForge/Wago upload.
- Packaging does not run inside the release-please job. A tag pushed with the default `GITHUB_TOKEN` does **not** start a tag workflow, and packaging on the branch push fails too: the packager reads the real `GITHUB_REF` (`refs/heads/main`) and skips with `Found future tag` (a step-level `env:` cannot override a reserved `GITHUB_*` variable). Instead the `package` job dispatches `release.yml` on the new tag - `workflow_dispatch` is the one event `GITHUB_TOKEN` may still start - so the packager runs with a real tag ref. `release.yml` stays `workflow_dispatch` only and doubles as the entry point for manual builds.
- `CHANGELOG.md` is **generated and accumulating** — release-please owns it. Do NOT hand-edit it and do NOT overwrite it with a single release's notes. The packager gets only the newest section, via `RELEASE_NOTES.md`, which CI extracts from `CHANGELOG.md` before packaging (it is gitignored and excluded from the zip).
- Version headings in `CHANGELOG.md` must stay in the `## [x.y.z]` form — the extraction stops at the next `## [` heading.
- Never edit the `## Version:` line in the TOC by hand — it sits inside `# x-release-please-start-version` / `# x-release-please-end` markers. The TOC holds bare semver (`1.2.0`); tags keep the `v` prefix (`v1.2.0`).
- `## X-DBM-Voice-Version:` is the **DBM sound registry version**, not the addon version. release-please does not touch it, and it must not be bumped for a release.
- **NEVER** delete, force-push, or recreate tags/releases. CurseForge picks up every tag push and creates duplicate entries that cannot be removed. Always let a new release PR produce the next version instead.

## Building the pack

Everything lives in `generation/`. Requirements: Python 3, ffmpeg on PATH, `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`.

```
python generation/bakeoff.py azure-polina     # render the whole table
python generation/build_countdown.py          # reassemble the countdown files
python generation/normalize_level.py          # even out the levels
python generation/check_pack.py               # offline release gate
python generation/build_review.py             # build the review page
python generation/serve.py                    # open it in a browser
```

- `ua_table.tsv` - `key<TAB>english<TAB>ukrainian[<TAB>spoken]`. The English lines come from `!VoiceText.txt` in DBM-Voicepack-Demo; the key list is `DBM-Core/VoicePackSounds.lua`. The optional fourth column is what the engine hears when it differs from what is written, e.g. `ДПС` spoken as `де-пе-ес`.
- `bakeoff.py` renders into `generation/variants/<id>/`, one folder per configuration, never overwriting. Retired configurations stay in the file as a record and no longer render.
- `build_countdown.py` must be re-run after regenerating `count/1..5`, or the countdown stays in the previous voice. Those four files are excluded from `normalize_level.py`: they are half silence by design, so their mean level says nothing about how loud the numbers are.
- `check_audio.py` runs every clip past Ukrainian ASR and a stress recogniser and ranks the rows by how far the transcript drifted. A row scores as the better of the two transcripts, because either model alone produces false alarms on one-second clips. It sees defects that change which word comes out, not accent or stress, so it produces a list to listen down rather than a verdict.
- `respell.py` proposes alternative spellings for rows the check distrusts. Its winners need a human: the score rewards clarity to a machine, and some winners change the meaning rather than the pronunciation.
- `models.py` keeps the two recognisers on F: and disables hub symlinks, which fail on this account with WinError 1314.
- `envvars.py` reads credentials from the live user environment, so `setx` takes effect without restarting the tooling.

## What the engine honours, measured

- Word order beats spelling hints. `Аура гніву` was read letter by letter as "а-у-ра"; `Гнівна аура` is read correctly.
- Capitalising the stressed vowel does **not** work. It won zero of ten rows in a controlled comparison, and on Azure it drags the stress onto the capitalised letter (`Багато стАків` stressed the А). An earlier version of this pack relied on it.
- A combining acute (U+0301) does nothing useful, and broke words outright on ElevenLabs.
- Slowing delivery does not reliably help: at -10% and -20% it moved recognition by ±0.1 either way and cost 10-20% of the length.
- Acronyms need a spoken form, not a spelling trick.
- Neural voices pad clips with silence, about 0.17 s in front and 0.90 s behind against 1.04 s of speech. Both are trimmed on the way to ogg: the front padding is a late warning, the back padding is nothing at all.
- Words spelled like another part of speech get read as the wrong one. `Перерви` came out as the noun, so interrupts say `Збий закляття`.

## Translation conventions

Short imperative callouts, no politeness. Ukrainian over transliteration wherever an equivalent of about the same length exists (`ади` and `моб` to `вороги`, `кік` to `збий`, `фронтал` to `конус`, `кайть` to `відбігай`, `таунт` to `забери`); words that are already Ukrainian (аура, портал, фаза) and settled loans (бос, танк, рейд) stay. Length is a feature: a replacement costing more than about 0.3 s has to earn it. The written line stays correct Ukrainian; when the engine mispronounces it, the fourth column changes what it hears, not what it says.

## TOC and countdown constraints

DBM builds sound paths as `Interface/AddOns/DBM-VP<ShortName>/<file>.ogg`, so the folder name must be `DBM-VP` plus ShortName exactly, or the pack is listed but silent.

WoW 12.x plays a single pre-assembled countdown file rather than the numbers one by one, and `DBM:GetCountSounds` only offers packs that provide one. That needs `X-DBM-Voice-MidnightCompat` in the TOC plus four files in `count/`: `fivecount.ogg` (5.000 s, numbers at 0-4 s), `threecount.ogg` (5.000 s, 2 s of silence then 3, 2, 1), and the `_5s` variants at 10.000 s for the 10-second highlight window.

`DBM-VPUkrainianTTS.lua` registers the event sounds: victory and wipe through `DBM:AddVictorySound` and `AddDefeatSound`, the pull and engage sounds through LibSharedMedia, which DBM-Core already loads.
