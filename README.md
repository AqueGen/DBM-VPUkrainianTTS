# DBM Ukrainian Voice Pack

Ukrainian voice for [Deadly Boss Mods](https://github.com/DeadlyBossMods/DBM-Retail). Female voice, fully generated with ElevenLabs TTS (models `eleven_multilingual_v2` / `eleven_turbo_v2_5`).

- 448 sounds: 391 alert phrases + 11 countdown numbers + 4 combined countdown files + 38 Grimrail Depot (Thogar) train callouts + 4 event sounds
- Voice pack version 19 (current DBM maximum), Interface 12.0.7 / 12.1.0
- Complete coverage of `DBM-Core/VoicePackSounds.lua` (all 429 keys)
- Ukrainian countdown in the "count sounds" dropdowns, plus Ukrainian victory, wipe, pull timer and engage sounds

## Install

Unpack `DBM-VPUkrainianTTS` into `Interface/AddOns`, then in game: `/dbm` -> Options -> Countdowns and Voice Packs -> set **Ukrainian Female TTS** as the voice pack for spoken alerts. The same entry is available for the count sound dropdowns; victory and wipe sounds live under Alerts -> Event Sounds, and the pull timer / engage sounds under Timer Bars -> Pull & Break as "Ukrainian: ...".

## How the voices were generated

Everything needed to regenerate or extend the pack is in `generation/`:

- `ua_table.tsv` - the full phrase table: `file<TAB>english<TAB>ukrainian`. English source texts come from `!VoiceText.txt` in [DBM-Voicepack-Demo](https://github.com/DeadlyBossMods/DBM-Voicepack-Demo); the canonical sound key list is `DBM-Core/VoicePackSounds.lua` (key -> voice version it was introduced in).
- `events_table.tsv` - same format, for the four event sounds (victory, wipe, pull, engage).
- `gen_voices.py` - generation script. Reads a table, calls ElevenLabs TTS, converts mp3 to ogg vorbis (q4, 44.1 kHz) with ffmpeg. Resumable: skips files that already exist, so deleting a single ogg and re-running regenerates just that file. Set `GEN_TABLE` to use a table other than `ua_table.tsv`.
- `build_countdown.py` - assembles the combined countdown files from the per-number oggs. No TTS calls, ffmpeg only.

Requirements: Python 3, ffmpeg on PATH, `ELEVENLABS_API_KEY` env var (a free-tier key with text-to-speech permission is enough).

```
python gen_voices.py                                    # long phrases, model eleven_multilingual_v2
GEN_SHORT=1 python gen_voices.py                        # 1-2 word phrases, eleven_turbo_v2_5 + language_code=uk
GEN_TABLE=events_table.tsv GEN_SHORT=1 python gen_voices.py   # the event sounds
python build_countdown.py                               # rebuild fivecount/threecount from count/1..5.ogg
```

Two modes exist because `eleven_multilingual_v2` auto-detects language and misreads short standalone Cyrillic words (e.g. "Один") as Russian; `eleven_turbo_v2_5` supports forcing `language_code=uk` but multilingual v2 does not.

### Adding new sounds when DBM bumps the voice version

1. Diff `VoicePackSounds.lua` against the files in this pack to find new keys.
2. Add rows to `generation/ua_table.tsv` with Ukrainian translations.
3. Run the script (it only generates missing files), copy new oggs into the addon, bump `X-DBM-Voice-Version` in the TOC.

### Countdown on WoW 12.x

DBM 12.x no longer plays `count/5.ogg` .. `count/1.ogg` one at a time for timeline countdowns; it plays a single pre-assembled file, and `DBM:GetCountSounds` only offers packs that provide one (`DBM-Core/modules/Sounds.lua`). A pack therefore needs `X-DBM-Voice-MidnightCompat` in the TOC and four extra files in `count/`, laid out exactly like `DBM-Core/Sounds/Corsica`:

| File | Length | Layout |
|---|---|---|
| `fivecount.ogg` | 5.000 s | numbers start at 0, 1, 2, 3, 4 s |
| `threecount.ogg` | 5.000 s | 2 s of silence, then 3, 2, 1 |
| `fivecount_5s.ogg` | 10.000 s | 5 s of silence, then the fivecount layout |
| `threecount_5s.ogg` | 10.000 s | 7 s of silence, then 3, 2, 1 |

The `_5s` variants are used when the timer highlight window is 10 s. `build_countdown.py` generates all four and asserts the resulting lengths.

### Event sounds

`DBM-VPUkrainianTTS.lua` registers the four sounds in `events/`. Victory and wipe use `DBM:AddVictorySound` / `DBM:AddDefeatSound`; the pull timer and engage dropdowns read from LibSharedMedia, so those two are registered with `LSM:Register`. The library is not embedded - DBM-Core already loads it, and `RequiredDeps: DBM-Core` guarantees the load order.

### TOC constraint

DBM builds sound paths as `Interface/AddOns/DBM-VP<X-DBM-Voice-ShortName>/<file>.ogg`, so the addon folder name MUST be `DBM-VP` + ShortName exactly (here: ShortName `UkrainianTTS`, folder `DBM-VPUkrainianTTS`). Mismatch = pack listed but silent.

### What the TTS engine does and does not honour

Learned the hard way while tuning pronunciation, all of it verified by ear against ElevenLabs:

- A combining acute accent (U+0301) **breaks** the word. The engine treats it as a foreign character rather than a stress mark, so `За́хист` comes out mis-stressed while plain `Захист` is read correctly. Never put accents in the table.
- **Capitalising the stressed syllable does work**: `Багато стАків` moves the stress where `стаків` alone lands it wrong. Use it only on words the engine gets wrong on its own - most words are fine untouched.
- A **trailing period** stops the last word being clipped, which happened on `Поглинь порожнечу`.
- Watch for words that are spelled the same as a different part of speech. `Перерви` is both the imperative of "interrupt" and a form of the noun "перерва"; the engine picked the noun, so those lines say `Збий закляття` instead.

### Translation conventions

- Short imperative raid callouts, no politeness.
- Gaming slang is transliterated from English pronunciation: "соук" (soak), "кік" (kick), "таунт" (taunt), "кайть" (kite), "ади" (adds), "АОЕ" in caps.

## Credits

- Voice generated with ElevenLabs (voice "Matilda") under the free tier.
- Phrase list: Deadly Boss Mods project.
