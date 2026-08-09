# Changelog

## [1.2.0](https://github.com/AqueGen/DBM-VPUkrainianTTS/releases/tag/v1.2.0)

- Reworked 22 alert lines after listening to them in game. `Перервай` was not a real word form and `Перерви` was read as the noun "перерва", so interrupts now say `Збий закляття`. `Соук` was a transliteration that does not exist in Ukrainian - soak lines use `Поглинь`. `helpkick`, `helpdispel` and `movesoon` now match what the English pack actually says.
- `positive`, `negative`, `harmonic` and `melodic` play when the charge or alignment lands on you (Raszageth, Lihuvim), so they name what you got: `Плюс`, `Мінус`, `Гармонія`, `Мелодія`.
- `enrage` and `crowdcontrol` are declared as dispel and interrupt warnings, so they now call the action instead of naming the effect.
- Fixed stress on `Багато стАків` and `стАкнутись`, and the clipped last word in `Поглинь порожнечу`.

## [1.1.1](https://github.com/AqueGen/DBM-VPUkrainianTTS/releases/tag/v1.1.1)

- First release built by the automated pipeline (tag -> CurseForge, Wago, GitHub Release). No changes to the sounds.

## [1.1.0](https://github.com/AqueGen/DBM-VPUkrainianTTS/releases/tag/v1.1.0)

- Ukrainian countdown for the DBM count sound dropdowns. WoW 12.x plays a single pre-assembled countdown file instead of the numbers one by one, so the pack now ships `fivecount`/`threecount` and their 10-second variants, built from the existing Ukrainian numbers.
- Four event sounds: victory and wipe (Alerts - Event Sounds), pull timer start and encounter engage (Timer Bars - Pull & Break, listed as "Ukrainian: ...").
- No changes to the 391 alert phrases.

## [1.0.4](https://github.com/AqueGen/DBM-VPUkrainianTTS/releases/tag/v1.0.4)

- First public release: 440 Ukrainian sounds generated with ElevenLabs text-to-speech - 391 alert phrases, 11 countdown numbers, 38 Grimrail Depot (Thogar) train callouts.
- Complete coverage of the current DBM sound registry (voice pack version 19), so no alert falls back to the default English voice.
- `colorchange`, `colorchangesoon` and `runtotrap` use the names DBM boss mods actually reference, unlike the VEM pack which still ships them under legacy names.
