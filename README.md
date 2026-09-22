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

Off by default: game menu -> Options -> AddOns -> **DBM Voice Ukrainian** -> **Текстові підказки**. **Формат підказки** next to it picks how the line reads: `Тег + фраза`, `Тільки тег` (`АОЕ`) or `Тільки фраза`.

The tags are: `АОЕ`, `ТАНК`, `ЗБИЙ`, `РОЗВІЙ`, `ПОГЛИНИ`, `АДДИ`, `ВІДІЙДИ`, `УХИЛЯЙСЯ`, `РОЗІЙДІТЬСЯ`, `ЗБЕРІТЬСЯ`, `СХОВАЙСЯ`, `ЙДИ`, `КОНТРОЛЬ`, `ДПС`, `ПРОЖМИ`, `ФАЗА`, `ВІДВЕРНИСЬ`.

Switching it on applies at once. Boss mods load per zone, so switching it on in a city means the text arrives with the first boss mod that loads - the pack says so in chat rather than asking for a reload it does not need. Switching it off, or changing the format after the text has run, does need a reload, and the pack offers one on the spot.

Two things worth knowing:

- DBM has to be showing renames at all. With `Use spell renames on announcement text` off in DBM -> Alerts -> Special Announcements nothing changes on screen, and the pack tells you so instead of failing quietly.
- The text also lands on timer bars. To keep real spell names there, switch off `Use spell renames on timer text` in DBM -> Timer Bars -> Bar Behavior.

Renames you make yourself with the **Rename** button in DBM's boss options still win over the pack. Warnings the boss mod ships without a voice line keep their spell name.

## Notes

Warnings are short imperative callouts, because a warning that arrives after the mechanic is useless. Borrowed gaming words are used only where Ukrainian has no equally short equivalent.

Found a phrase that sounds wrong? [Open an issue](https://github.com/AqueGen/DBM-VPUkrainianTTS/issues) with the line you heard. Translation fixes are welcome.

Phrase list from the Deadly Boss Mods project.
