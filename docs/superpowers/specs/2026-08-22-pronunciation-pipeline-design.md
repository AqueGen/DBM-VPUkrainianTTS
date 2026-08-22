# Pronunciation pipeline: per-row engines, immutable takes, automated checks

Status: approved 2026-08-22. Supersedes the ad-hoc "regenerate everything and listen to it" workflow.

## Problem

68 of the pack's 449 phrases were flagged by ear as badly pronounced. Two failure modes dominate: the engine reads Ukrainian with Russian vowels (most visibly `и`), and lexical stress lands on the wrong syllable. Fixing them one at a time by listening does not scale, does not survive a future voice change, and gives no way to tell whether a regenerated file got better or worse.

The pipeline must therefore encode what "pronounced correctly" means well enough that a machine can reject a bad take, and must never silently rewrite a take that was already accepted.

## What the bake-off settled

Ten phrases covering the failure modes were rendered through five configurations and picked by ear (`generation/picks.tsv`, round 1):

- **ElevenLabs wins.** `eleven_turbo_v2_5` with `language_code: uk` took 6 rows, `eleven_v3` took 4. The free `edge-tts` uk-UA-PolinaNeural voice won nothing, which answers the "is there a good free option" question with data rather than opinion.
- **Capitalising the stressed vowel is not the lever.** The `v3-caps` column won zero rows. An earlier note in CLAUDE.md credited this trick; on a controlled comparison it does not carry its weight, so no rules layer will be built on it.
- **`language_code` must not be sent to `eleven_v3`.** The response was byte-identical in size to `eleven_flash_v2_5`, i.e. the parameter silently routes the request to a different model. Only turbo and flash take it.
- **`eleven_v3` is not reproducible on short input.** Three renders of `Дякую` came back at 0.64 s, 1.84 s and 1.92 s - a 200% spread - while `Приманюй зараз` was identical every time. `eleven_turbo_v2_5` stayed within 11% on the same word. A take accepted by ear cannot be assumed to come back the same way.

A second round held the engine constant and varied the wording, so jargon could be judged against plain Ukrainian without the model confounding it. Result: keep the borrowed words almost everywhere; three lines change (`Кайть` -> `Відбігай`, `Скоро АОЕ` -> `Скоро шкода по площі`, `Іди в мілі` -> `Іди в ближній бій`). Plain wording costs 0.2-0.6 s per line, and a warning that arrives after the mechanic is worse than one with a borrowed word in it.

## Architecture

### 1. The table is the source of truth

`generation/ua_table.tsv` gains a fourth column, `engine`. Empty means the default (`turbo-uk`). Rows that need the other model carry `v3`.

A one-time migration writes `v2-legacy` into that column for every row already shipped, naming the model those files were actually made with. The 380 phrases nobody complained about are therefore left alone by construction, not by remembering to leave them alone.

### 2. Fingerprints decide what gets regenerated

`generation/state.json` maps each key to the SHA-256 of `(text, engine, voice)` - the engine id already pins the model and its parameters - plus the resulting duration and the last check result. A file is regenerated when, and only when, its fingerprint no longer matches. `--force <key>` overrides this for a single row.

This makes the audio the artifact and the table row its source. Changing the voice in the future invalidates every fingerprint at once, so a full regeneration stays possible - but as a deliberate act rather than an accident.

### 3. Generation takes more than one shot where the engine is unstable

Rows whose engine is known to wobble (short text on `v3`) are rendered three times; the take that passes the checks and sits closest to the median duration is kept. Stable rows keep the current single-shot path.

### 4. `check.py` is the gate

Four layers, each reporting which one rejected a take and why:

1. **Text lint** - combining acute U+0301 (breaks the engine outright), Russian-only letters `ы ъ э ё`, the wrong apostrophe character, implausible length.
2. **ASR round-trip** - ElevenLabs Scribe v2 transcribes the generated audio; after normalisation the transcript must equal the text that was sent. This catches a swallowed word and a Russian-accented reading alike, because either one makes the transcript diverge. Ukrainian sits in Scribe's top accuracy tier (<= 5% WER) and a full pass over the pack is 10.3 minutes of audio, about $0.04.
3. **Clipping** - the last word missing from the transcript, or the waveform ending on non-trivial energy.
4. **Stress (experimental)** - Scribe returns character-level timestamps, so each vowel's duration is measurable and the stressed vowel in Ukrainian is markedly longer. This layer ships **only if it separates the 68 flagged phrases from the accepted ones**; the flagged list is a labelled data set, so the claim is testable. If it does not separate them it is deleted, and the report says so rather than leaving a check nobody trusts.

### 5. The human reviews what the machine could not judge

`check.py` results feed a column in `generation/review.html`: `ok`, or the reason for rejection. Listening is then spent on suspicious rows instead of all 449. Every regeneration round remains a new column, so previous attempts stay comparable.

## First pass

1. Migrate the table (add `engine`, adopt the legacy rows).
2. Apply the three wording changes.
3. Regenerate the 68 flagged phrases - the ten judged in the bake-off with their picked engine, the remaining 58 with the default.
4. Run `check.py` over the regenerated set.
5. Calibrate the stress layer against the flagged and accepted phrases; keep or drop it on the numbers.
6. Publish the round as a new column, accept by ear, ship the accepted takes, bump the version, release.

## Testing

Unit tests cover `check.py`'s logic with no network and no spend: text normalisation, each lint rule, and the stress heuristic against synthetic timing data. The ASR pass itself is a manual integration run - it needs a key and costs money, so it stays out of any automated suite.

## Deferred

An automatic stress dictionary (`lang-uk/ukrainian-tts-preprocessing`, Apache 2.0, offline) feeding IPA hints into `eleven_v3`, so stress is dictated rather than inspected. Deferred because v3's IPA support is documented at 80-90% consistency and v3 already proved unreliable on short input here. The cheap way to find out is one more bake-off column on the same ten phrases; if it holds stress, this is built on top of the design above rather than instead of it.

## Risks

- Scribe's character-level timestamps may be coarser than the vowel durations the stress layer needs. The calibration step is what surfaces this; the layer is designed to be droppable.
- Two engines in one pack may be audible as a timbre shift between phrases. Both use the same voice, and the review page is where that gets judged; if it grates, the fallback is a single engine for everything at the cost of the four `v3` rows.
- ASR round-trip cannot catch a phrase that is pronounced clearly and wrongly stressed, which is exactly why the stress layer is being attempted rather than assumed unnecessary.
