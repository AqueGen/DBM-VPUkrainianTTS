# Pronunciation pipeline: per-row engines, immutable takes, honest gates

Status: revised and approved 2026-08-22, after two independent adversarial reviews of the first draft. The revision is substantial: the first draft claimed an ASR round-trip could detect accent errors and proposed an automated stress check. Both claims failed review and are gone. What replaces them is smaller and provable.

## Problem

66 of the pack's 449 phrases were rejected by ear (`generation/flagged.txt`). Two failure modes: the engine reads Ukrainian with Russian phonetics (most visibly `и`), and lexical stress lands on the wrong syllable. Fixing them one at a time by listening does not scale, does not survive a future voice change, and gives no way to tell whether a regenerated file got better or worse.

## What the bake-off settled

Ten phrases covering the failure modes were rendered through five configurations and picked by ear (`generation/picks.tsv`):

- **ElevenLabs wins.** `eleven_turbo_v2_5` with `language_code: uk` took 6 rows, `eleven_v3` took 4. `edge-tts` with the `uk-UA-PolinaNeural` voice took none. That result is scoped to that one free voice on these ten phrases; it is not a claim that no good free engine exists.
- **Capitalising the stressed vowel is not the lever.** The `v3-caps` column won zero rows. An earlier note in CLAUDE.md credited this trick; on a controlled comparison it does not carry its weight, so no rules layer is built on it.
- **`language_code` must not be sent to `eleven_v3`.** The response was byte-identical in size to `eleven_flash_v2_5`, i.e. the parameter silently routes the request to another model. Only turbo and flash take it.
- **`eleven_v3` is not reproducible on short input.** Three renders of `Дякую` came back at 0.64 s, 1.84 s and 1.92 s - a 200% spread - while `Приманюй зараз` was identical all three times. `eleven_turbo_v2_5` stayed within 11% on the same word.

A second round held the engine constant and varied the wording. Result: keep the borrowed words almost everywhere; three lines change (`Кайть` -> `Відбігай`, `Скоро АОЕ` -> `Скоро шкода по площі`, `Іди в мілі` -> `Іди в ближній бій`). Plain wording costs 0.2-0.6 s per line, and a warning that arrives after the mechanic is worse than one carrying a borrowed word.

## What the review changed

Both reviewers, independently, rejected the same things. Recorded here because the temptation to re-add them will return:

1. **An ASR round-trip cannot detect an accent error.** Scribe answers "which words were spoken", not "with which phones". A Russian-coloured `и` does not change which word was said, and the language model resolves the transcript to the correct spelling precisely because no other word is plausible. Worse, exact matching produces false rejections: at 5% WER a two-word phrase clears an exact comparison only about 90% of the time. ASR is therefore a **content check** - it catches a swallowed, substituted or hallucinated word - and nothing more, until an experiment says otherwise.
2. **Fingerprinting the recipe does not protect the take.** A stochastic engine turns one recipe into many different outputs, so a recipe hash cannot identify which render a human accepted, and any path that rewrites an `.ogg` without touching the table stays invisible. One such path already exists: `gen_voices.py` in `GEN_SHORT` mode deletes and re-renders. Acceptance must be recorded against the audio bytes.
3. **The stress check has no valid feature and no ground truth.** Duration is confounded by phrase-final lengthening, which dominates in 1-3 s clips; character timestamps are alignment output, not phone boundaries, and `я ю є ї` are not single phones. Above all, nothing in the project knows where stress *belongs* - that is a stress dictionary, which the first draft deferred as a generation-side nicety without noticing the check needs it as ground truth. And the labels say "this phrase is bad", not "this vowel is mis-stressed", so a calibration against them could pass by learning phrase length.
4. **Median-of-three selection is not a quality signal.** Duration does not rank pronunciation. Four rows use `v3`; a human ear settles them in seconds.
5. **"Listen only to suspicious rows" is unsafe while the detectors are blind to accent.** Every newly generated take is auditioned before it ships.

## Architecture

### 1. The table is the source of truth

`generation/ua_table.tsv` gains a fourth column, `engine`. Empty means the default (`turbo-uk`). Rows that need the other model carry `v3`.

A one-time migration writes `v2-legacy` into that column for every row already shipped, naming the model those files were actually made with. `v2-legacy` is **provenance, not a recipe**: it exists so that existing files are recognised rather than regenerated, and any row that does get regenerated is rendered with the current default engine instead. Without that rule the first deliberate full regeneration would resurrect `eleven_multilingual_v2` - the model whose Russian reading of short Cyrillic text started this whole exercise.

### 2. Takes are immutable, acceptance is a hash of the shipped audio

Every render lands at `generation/takes/<key>/<round>-<n>.ogg` and is never overwritten. `generation/accepted.json` maps each key to the take that was accepted: its SHA-256, its take path, the round it came from, and the date. The file that ships in the pack root is a copy of that take, written to a temporary name and renamed into place so a crash cannot leave a half-written `.ogg`.

`check.py` verifies that the shipped bytes still hash to the accepted value. "An accepted take was silently replaced" therefore becomes a detected state instead of an invisible one, and previous rounds stay listenable because their takes still exist.

### 3. The recipe fingerprint decides what needs a new take - and nothing more

`generation/state.json` records, per key, the SHA-256 of the canonical tuple `(text, model_id, voice_id, language_code, output_format, recipe_version)`. A row needs a new take when its fingerprint no longer matches the one the accepted take was made from, or when it has no accepted take at all.

This is deliberately a *staleness* signal, not a claim of reproducibility: ElevenLabs may change what sits behind a model id at any time, which is unhashable, and that is exactly why acceptance rides on the audio hash. `recipe_version` is a hand-bumped integer for changes in the generator that alter output but are invisible in the tuple.

A take that failed its checks is recorded as failed, so the next ordinary run retries it instead of concluding the fingerprint matches and doing nothing.

### 4. `check.py` gates what can actually be measured

Every layer reports `pass`, `fail` or `not run`, and `not run` is never treated as success. Release refuses a pack in which a mandatory layer did not run.

**Offline, free, mandatory:**
- **Inventory** - every table key has exactly one audio file, no orphans, no duplicate keys. The four countdown files (`count/fivecount`, `count/threecount` and their `_5s` variants) are assembled by `build_countdown.py` from the digit clips rather than synthesised, so they are expected extras rather than orphans: 449 table rows + 4 event rows + 4 assembled = 457 files.
- **Container** - decodes, is Ogg Vorbis, 44.1 kHz, mono/stereo as the rest of the pack.
- **Loudness** - `mean_volume` within 1.5 dB of the pack's own level. Measured: the shipped pack sits at -21.6 dB, `turbo-uk` at -22.7 dB (inaudible), `eleven_v3` at -19.3 dB and up to -16.6 dB on single rows, which is an audible jump. Out-of-band takes get a fixed gain applied rather than a dynamics pass, so the timbre is untouched.
- **Silence** - leading silence over 0.15 s (a warning that starts late is the defect this pack exists to avoid) and trailing silence over 0.4 s.
- **Duration** - spoken phrases cap at 4.5 s; measured distribution is median 1.25 s, p95 2.04 s, longest real phrase 4.27 s (`Thogar/B2A4`). The countdown compilations are exempt: they are 5.000 s and 10.000 s by construction.
- **Text lint** - combining acute U+0301 (which breaks the engine outright), Russian-only letters `ы ъ э ё`, the wrong apostrophe character, implausible length.
- **Truncation** - the waveform must not end on significant energy, which is what a cut-off take looks like.

**Networked, paid, advisory:**
- **ASR content check** - Scribe v2 transcribes the take and the transcript is compared to the text that was sent. A divergence means a word was swallowed, substituted or hallucinated. It is advisory: a mismatch marks the row for the ear, it does not by itself reject a take, because the false-rejection rate on short phrases is real. It says nothing about accent. Cost is $0.22/h of audio, about $0.04 for the whole pack.

### 5. The ear accepts every new take

`check.py` results become a column in `generation/review.html`, and each round of takes becomes a column beside the previous ones. The human listens to the new takes, picks the winner per row, and exports the picks; a small script turns that export into `accepted.json` entries and copies the winning takes into the pack.

Nothing about untouched rows changes: their acceptance was granted once and stays until their text or engine changes.

## Experiment E1: is ASR blind to accent here?

Blocked on the API key gaining the `speech_to_text` permission - it currently returns `401 missing the permission speech_to_text`.

Transcribe the 66 flagged files and an equally sized random sample of accepted ones, and measure how often the transcript diverges from the expected text in each group. Declared in advance: if at least 60% of flagged rows diverge while at most 10% of accepted rows do, ASR carries real signal about these defects and may be promoted from advisory to a gate. Anything less and it stays a content check, and the finding is written down here rather than quietly forgotten.

Cost: about $0.01 for the two groups. This is the cheapest question in the project and it decides how much listening the owner can ever be spared.

## First pass

1. Migrate the table: add `engine`, write `v2-legacy` on shipped rows, `v3` on the four rows the bake-off picked.
2. Apply the three wording changes.
3. Build the take store and `accepted.json` by adopting the current shipped audio (hash what is there today; nothing is regenerated).
4. Regenerate the 66 flagged rows into round 1 of the take store - the ten judged in the bake-off with their picked engine, the remaining 56 with the default.
5. Run `check.py`; fix what the offline gates reject (gain, trimming, or a retry).
6. Publish the round as a column in the review page, audition, pick, accept.
7. Ship accepted takes, bump the version through release-please, release.

E1 runs as soon as the permission exists; if it lands before step 6 its result is applied to how much of step 6 needs the ear.

## Testing

`pytest` (already installed, 9.0.3) over the offline logic: the fingerprint tuple and its canonical serialisation, staleness decisions, inventory reconciliation, each lint rule, loudness and silence and duration gates against generated fixtures, and the accepted-hash verification including the "file was replaced behind our back" case. No network, no spend.

The ASR pass is a separate command run by hand; its transcripts are kept so a verdict can be re-examined without paying again.

## Deferred

- **Automated stress detection.** Needs three things this project does not have: a stress dictionary as ground truth, per-phrase labels naming the actual defect rather than "bad", and phone-level alignment rather than character timestamps. Days of work, and worth revisiting only if E1 or the ear says stress is still the dominant complaint after the regeneration.
- **IPA hints for `eleven_v3`.** Documented at 80-90% consistency, and v3 already proved unreliable on short input. The cheap probe is one more bake-off column on the same ten phrases.

## Risks

- Two engines in one pack may read as a timbre shift between phrases. Both use the same voice; the loudness gate removes the level component; the ear judges the rest. Fallback is a single engine at the cost of the four `v3` rows.
- The default engine is credited with fixing 56 flagged rows on the evidence of ten. If it does not, those rows need rewording or a different engine, and the take store makes that a cheap second round rather than a rewrite.
- No automated check in this design detects a clearly spoken, wrongly stressed phrase. That is a known, stated hole, not an oversight.
