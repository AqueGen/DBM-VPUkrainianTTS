# Translation audit, 2026-08-23

Every row of `ua_table.tsv` read against its English source line. Only rows worth changing are listed; the rest are faithful. Nothing here is applied yet.

## Wrong meaning

| key | english | now | proposed | why |
|---|---|---|---|---|
| `linesoon` | link incoming | Скоро лінія | Скоро зв'язок | The source says **link**, not line. `lineyou` / `lineapart` / `linegather` really are about a line; this one is a different mechanic and got swept in with them. |
| `enrage` | enrage | Зніми лють. | Лють | The Ukrainian invents an instruction ("remove the rage") that the source does not give. DBM says the boss enraged; deciding what to do about it is the player's business. |
| `sparktowater` | Kite spark to water | Кайть іскру до води | Веди іскру до води | Carries the same `кайть` you have already rejected in the `kite` row. |

## Engine hacks that should not survive an engine change

Both were added to fight ElevenLabs and are now known not to work, or not to be needed.

**Capitalised stress hints** - the `v3-caps` column of the bake-off won zero rows out of ten, so the trick does not earn its place. On a different engine a mid-word capital is more likely to be read as an abbreviation than as stress.

| key | now | proposed |
|---|---|---|
| `dshigh` | Багато стАків. | Багато стаків |
| `gather` | стАкнутись. | Стакнутись |

**Trailing full stops** - ten rows carry one, added so ElevenLabs would not clip the last word: `dshigh`, `enrage`, `gather`, `helpdispel`, `helpkick`, `holdingorb`, `interruptbyeye`, `kickcast`, `kickorstopcast`, `voidsoak`. On a neural voice a full stop usually buys a pause instead, which costs time in combat. Strip them, then listen: if a word gets clipped again, put the stop back on that row alone.

## Inconsistent pairs

The same English rendered two ways. Neither is wrong; picking one makes the pack sound deliberate.

| english | keys | now |
|---|---|---|
| quake | `quake` vs `stompsoon` / `stompstart` | Землетрус vs Струс |
| stack | `gather` vs `gathershare` | стАкнутись vs Збирайтесь разом |
| stop attacking | `stopatk` vs `stopattack` | Припини атакувати vs Припини атаку |
| keep moving | `cntnuemove` vs `keepmove` | Продовжуй рух vs Продовжуй рухатись |

## Weak but not wrong

| key | english | now | comment |
|---|---|---|---|
| `lowsanity` | Low Sanity | Низький розсудок | Reads like a medical chart. "Розсудок падає" is what a person would say. |
| `getknockedup` | Get Knocked Upward | Підкидання | The source is an instruction ("let it throw you"), the translation is a noun naming the effect. Same for `carefly` (knocking back -> Відкидання). |
| `takedamage` | take damage | Прийми шкоду | Literal. The mechanic means "stand in it on purpose"; "Прийми удар" sounds like an order rather than a stat. |
| `toxic` | Toxic | Токсичний | A bare adjective with nothing to agree with. |

## Deliberately left alone

`di` / `didi` are opaque in the source too, so transliteration is as good as anything. `bouncer`, `cleaner`, `entertainer`, `server` are a themed set of staff roles and read correctly as Викидайло / Прибиральник / Артист / Офіціант. `shadowrun` adds "тікай" that the source lacks, but that is what separates it from `shadowyou`, which carries the identical English line.
