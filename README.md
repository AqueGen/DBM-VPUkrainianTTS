# DBM Ukrainian Voice Pack

Ukrainian voice for [Deadly Boss Mods](https://github.com/DeadlyBossMods/DBM-Retail) in World of Warcraft. Boss warnings, the countdown, and the victory, wipe, pull and engage sounds, all spoken in Ukrainian.

The voice is synthetic: `uk-UA-PolinaNeural` from Azure AI Speech, a voice trained on Ukrainian rather than an English one reading Ukrainian words.

## Install

Unpack `DBM-VPUkrainianTTS` into `Interface/AddOns`, then in game:

- `/dbm` -> Options -> Countdowns and Voice Packs -> pick **Ukrainian Female TTS** for spoken alerts
- the same entry appears in the count sound dropdowns
- victory and wipe live under Alerts -> Event Sounds
- the pull timer and engage sounds under Timer Bars -> Pull & Break, as "Ukrainian: ..."

DBM-Core must be installed; the pack needs nothing else.

## Action text on screen

DBM writes the spell name on screen while the pack says what to do. The pack can put the spoken line on screen instead, so the warning reads `АОЕ | Скоро шкода по площі` rather than `Rage of the Shackled`.

Off by default. Game menu -> Options -> AddOns -> **DBM Voice Ukrainian**:

- **Текстові підказки** - turn the on-screen text on, or type `/uatext`
- **Формат підказки** - `Тег + фраза`, `Тільки тег` (`АОЕ`) or `Тільки фраза`. The tags are `АОЕ`, `ТАНК`, `ЗБИЙ`, `РОЗВІЙ`, `ПОГЛИНИ`, `АДДИ`, `ВІДІЙДИ`, `УХИЛЯЙСЯ`, `РОЗІЙДІТЬСЯ`, `ЗБЕРІТЬСЯ`, `СХОВАЙСЯ`, `ЙДИ`, `КОНТРОЛЬ`, `ДПС`, `ПРОЖМИ`, `ФАЗА`, `ВІДВЕРНИСЬ`
- **Не чіпати смуги таймерів** - keeps real spell names on the timer bars
- **Прослухати** - plays a sample and prints the line the way your settings render it

Switching the text on applies at once. Boss mods load per zone, so if you switch it on in a city the text arrives with the first boss mod that loads - the pack says so in chat rather than asking for a reload it does not need. Switching it off or changing the format after the text has run does need a reload, and the pack offers one on the spot. Swapping to a spec with a different role needs one too, but that only earns a line in chat - a dialog on every spec swap is not worth it.

DBM has to be showing renames at all: with `Use spell renames on announcement text` off in DBM -> Alerts -> Special Announcements, nothing changes on screen, and the pack tells you so instead of failing quietly.

Tank, healer and damage specs get different wording where the role changes what you do: a tank reads `ТАНК | Прожми захист`, everyone else reads `ТАНК | Танк під ударом`. Dodges and run-outs read the same for everyone.

Renames you make yourself with the **Rename** button in DBM's boss options still win over the pack. Warnings the boss mod ships without a voice line keep their spell name.

## Notes

Warnings are short imperative callouts, because a warning that arrives after the mechanic is useless. Borrowed gaming words are used only where Ukrainian has no equally short equivalent.

Found a phrase that sounds wrong? [Open an issue](https://github.com/AqueGen/DBM-VPUkrainianTTS/issues) with the line you heard. Translation fixes are welcome.

Phrase list from the Deadly Boss Mods project.
