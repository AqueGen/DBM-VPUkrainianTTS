# DBM Ukrainian Voice Pack

Ukrainian voice for [Deadly Boss Mods](https://github.com/DeadlyBossMods/DBM-Retail). A synthetic female voice, generated with Azure AI Speech (`uk-UA-PolinaNeural`) - a voice trained on Ukrainian speech rather than an English one reading Ukrainian.

- 457 sounds: 449 alert phrases (including 11 countdown numbers and 38 Grimrail Depot train callouts), 4 combined countdown files and 4 event sounds
- Voice pack version 20 (current DBM maximum), Interface 12.0.7 / 12.1.0
- Complete coverage of `DBM-Core/VoicePackSounds.lua`
- Ukrainian countdown in the "count sounds" dropdowns, plus Ukrainian victory, wipe, pull timer and engage sounds

## Install

Unpack `DBM-VPUkrainianTTS` into `Interface/AddOns`, then in game: `/dbm` -> Options -> Countdowns and Voice Packs -> set **Ukrainian Female TTS** as the voice pack for spoken alerts. The same entry is available for the count sound dropdowns; victory and wipe sounds live under Alerts -> Event Sounds, and the pull timer / engage sounds under Timer Bars -> Pull & Break as "Ukrainian: ...".

## How the pack is made

Everything needed to regenerate or extend it lives in `generation/`:

- `ua_table.tsv` - the phrase table: `key<TAB>english<TAB>ukrainian[<TAB>spoken]`. The English source lines come from `!VoiceText.txt` in [DBM-Voicepack-Demo](https://github.com/DeadlyBossMods/DBM-Voicepack-Demo); the canonical key list is `DBM-Core/VoicePackSounds.lua`. The optional fourth column is what gets synthesised when it differs from what is written - "ДПС" is spelled the way a player writes it and handed to the engine as "де-пе-ес", because otherwise it is read as an expanded government acronym.
- `events_table.tsv` - the same format for the four event sounds.
- `bakeoff.py` - renders the table through an engine into `generation/variants/<id>/`, one folder per configuration. Nothing is overwritten: a new setting means a new id, so every attempt stays comparable. Azure, edge-tts and local Piper voices are supported; retired configurations stay in the file as a record and no longer render.
- `build_countdown.py` - assembles the combined countdown files from the per-number clips. ffmpeg only, no synthesis. **Re-run it after regenerating `count/1..5`**, or the countdown will still be in the previous voice.
- `models.py` - downloads the local recognisers and Piper voices into a cache outside the repo.
- `envvars.py` - reads credentials from the live user environment, so a `setx` takes effect without restarting the tooling.

Requirements: Python 3, ffmpeg on PATH, and `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` for synthesis. The Standard (S0) tier includes 500,000 characters of neural TTS per month at no cost - the whole pack is about 9,000 - and unlike the free tier it grants the right to use the output in a published addon.

```
python generation/bakeoff.py azure-polina     # render the pack
python generation/build_countdown.py          # rebuild the assembled countdowns
python generation/build_review.py             # build the review page
python generation/serve.py                    # open it in a browser
```

## Reviewing by ear, and by machine

`generation/review.html` lists every phrase with its English source, its Ukrainian line, and a play button per rendering. A whole-pack rendering gets its own column with a **play all** button that walks the column top to bottom - space pauses, arrows step and rewind, `f` flags the row that is playing. 453 phrases are not worth 453 clicks.

`check_audio.py` listens to a column with two local models - Ukrainian ASR and a stress-mark recogniser - and ranks the rows by how far the transcript drifted from the text that was sent. It catches the defects that change *which* word comes out: "Вайп" transcribing as "вайпи", a swallowed word, a clipped ending. It cannot judge whether a correctly recognised word carries the right colouring, and it has no stress dictionary to compare against, so the output is a list to listen down rather than a pass/fail gate. A row scores as the better of the two transcripts, because either model alone produces false alarms on one-second clips.

`respell.py` is the other half: it synthesises several spellings of a line the check distrusted, scores each the same way, and publishes the winner as its own column. Its picks are proposals - the score measures whether a machine can make out the words, so a stiff but clear reading wins on points, and a winner sometimes changes the meaning rather than the pronunciation.

## What the engine does and does not honour

Measured on this pack, not assumed:

- **Word order beats spelling hints.** "Аура гніву" was read letter by letter, as "а-у-ра"; "Гнівна аура" is read correctly. The same fix worked for all three aura lines.
- **A combining acute accent (U+0301) does nothing useful.** It neither fixed the stress in "Погна́ли" nor survived on ElevenLabs, where it actively broke the word.
- **Capitalising the stressed syllable does not work.** An earlier version of this pack relied on it; a controlled comparison gave it zero wins out of ten, and on Azure it drags the stress onto the capitalised letter - "Багато стАків" stressed the А.
- **Slowing the delivery does not reliably help.** Tried at -10% and -20% across eight problem lines, it moved recognition by ±0.1 in both directions, and costs 10-20% of the phrase length.
- **Acronyms need a spoken form**, not a spelling trick: "ДПС" is read as a government agency unless the fourth column hands over "де-пе-ес".
- **Neural voices pad clips with silence.** Azure adds about 0.17 s in front and 0.90 s behind against 1.04 s of speech. The front padding is a late warning and the back padding is nothing at all, so both are trimmed on the way to ogg.
- Watch for words spelled like a different part of speech. `Перерви` is both the imperative "interrupt" and a form of the noun "перерва"; the engine picks the noun, so those lines say `Збий закляття`.

## Translation conventions

- Short imperative raid callouts, no politeness.
- Ukrainian over transliteration. Borrowed words are replaced wherever an equivalent of about the same length exists: `ади`/`моб` -> `вороги`, `кік` -> `збий`, `фронтал` -> `конус`, `кайть` -> `відбігай`, `таунт` -> `забери`. Words that are Ukrainian already (аура, портал, фаза) and loans the dictionaries have settled (бос, танк, рейд) stay.
- Length is a feature. A warning that arrives after the mechanic is worse than one carrying a borrowed word, so a replacement that costs more than about 0.3 s has to earn it.
- The written line stays correct Ukrainian; when the engine mispronounces it, the fourth column changes what it hears, not what it says.

## TOC constraint

DBM builds sound paths as `Interface/AddOns/DBM-VP<X-DBM-Voice-ShortName>/<file>.ogg`, so the addon folder name MUST be `DBM-VP` + ShortName exactly (here: ShortName `UkrainianTTS`, folder `DBM-VPUkrainianTTS`). A mismatch leaves the pack listed but silent.

## Countdown on WoW 12.x

DBM 12.x no longer plays `count/5.ogg` .. `count/1.ogg` one at a time for timeline countdowns; it plays a single pre-assembled file, and `DBM:GetCountSounds` only offers packs that provide one (`DBM-Core/modules/Sounds.lua`). A pack therefore needs `X-DBM-Voice-MidnightCompat` in the TOC and four extra files in `count/`, laid out exactly like `DBM-Core/Sounds/Corsica`:

| File | Length | Layout |
|---|---|---|
| `fivecount.ogg` | 5.000 s | numbers start at 0, 1, 2, 3, 4 s |
| `threecount.ogg` | 5.000 s | 2 s of silence, then 3, 2, 1 |
| `fivecount_5s.ogg` | 10.000 s | 5 s of silence, then the fivecount layout |
| `threecount_5s.ogg` | 10.000 s | 7 s of silence, then 3, 2, 1 |

The `_5s` variants are used when the timer highlight window is 10 s. `build_countdown.py` generates all four and asserts the resulting lengths.

## Event sounds

`DBM-VPUkrainianTTS.lua` registers the four sounds in `events/`. Victory and wipe use `DBM:AddVictorySound` / `DBM:AddDefeatSound`; the pull timer and engage dropdowns read from LibSharedMedia, so those two are registered with `LSM:Register`. The library is not embedded - DBM-Core already loads it, and `RequiredDeps: DBM-Core` guarantees the load order.

## Credits

- Voice: Azure AI Speech, `uk-UA-PolinaNeural`. Every line in this pack is synthetic speech, not a recording of a person.
- Phrase list: the Deadly Boss Mods project.
