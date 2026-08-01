# DBM Voice Pack: Ukrainian Matilda (TTS)

Ukrainian female voice pack for [Deadly Boss Mods](https://github.com/DeadlyBossMods/DBM-Retail), fully generated with ElevenLabs TTS (voice "Matilda", model `eleven_multilingual_v2` / `eleven_turbo_v2_5`).

- 440 sounds: 391 alert phrases + 11 countdown + 38 Grimrail Depot (Thogar) train callouts
- Voice pack version 19 (current DBM maximum), Interface 12.0.7 / 12.1.0
- Successor to the abandoned [DBM Voice Pack (Ukrainian Female)](https://www.curseforge.com/wow/addons/dbm-voice-pack-ukrainian-female) which is stuck at voice version 17 / WoW 11.x

## Install

Unpack `DBM-VPUkrainianTTS` into `Interface/AddOns`, then in game: `/dbm` -> Options -> Spoken Alerts -> select **Ukrainian Matilda (TTS)**.

## How the voices were generated

Everything needed to regenerate or extend the pack is in `generation/`:

- `ua_table.tsv` - the full phrase table: `file<TAB>english<TAB>ukrainian`. English source texts come from `!VoiceText.txt` in [DBM-Voicepack-Demo](https://github.com/DeadlyBossMods/DBM-Voicepack-Demo); the canonical sound key list is `DBM-Core/VoicePackSounds.lua` (key -> voice version it was introduced in).
- `gen_voices.py` - generation script. Reads the table, calls ElevenLabs TTS, converts mp3 to ogg vorbis (q4, 44.1 kHz) with ffmpeg. Resumable: skips files that already exist, so deleting a single ogg and re-running regenerates just that file.

Requirements: Python 3, ffmpeg on PATH, `ELEVENLABS_API_KEY` env var (a free-tier key with text-to-speech permission is enough).

```
python gen_voices.py              # long phrases, model eleven_multilingual_v2
GEN_SHORT=1 python gen_voices.py  # 1-2 word phrases, eleven_turbo_v2_5 + language_code=uk
```

Two modes exist because `eleven_multilingual_v2` auto-detects language and misreads short standalone Cyrillic words (e.g. "Один") as Russian; `eleven_turbo_v2_5` supports forcing `language_code=uk` but multilingual v2 does not.

### Adding new sounds when DBM bumps the voice version

1. Diff `VoicePackSounds.lua` against the files in this pack to find new keys.
2. Add rows to `generation/ua_table.tsv` with Ukrainian translations.
3. Run the script (it only generates missing files), copy new oggs into the addon, bump `X-DBM-Voice-Version` in the TOC.

### Translation conventions

- Short imperative raid callouts, no politeness.
- Gaming slang is transliterated from English pronunciation: "соук" (soak), "кік" (kick), "таунт" (taunt), "кайть" (kite), "ади" (adds), "АОЕ" in caps.
- A combining acute accent (U+0301) controls stress where the TTS guesses wrong, e.g. "Ста́кнутись".

## Credits

- Voice: ElevenLabs "Matilda", generated under the ElevenLabs free tier.
- Phrase list: Deadly Boss Mods project.
