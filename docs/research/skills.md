# Skills Research

Last updated: 2026-07-16

## Combat Art Skill Evidence

What was discovered:
- `SkillParam.csv` contains skill rows, prerequisite-like row references, a `SkillDescriptionId`, an `EventFlagId`, and an `Unk1` field that links many Combat Art skills to `EquipParamWeapon` rows.
- Rows `701` through `792` are Prosthetic Tool upgrades and remain handled by `data/sekiro/prosthetic-upgrades.json`, not by the Skills analyzer.
- The first verified Skills analyzer batch covers Combat Arts whose `SkillParam.Unk1` value links to a named `EquipParamWeapon` Combat Art row.
- In `S0000.sl2`, the same weapon inventory record pattern used for Prosthetic Tools identifies 6 / 18 mapped Combat Arts as unlocked and 12 / 18 as missing.
- `SkillParam.EventFlagId` is not used as skill ownership evidence yet. Most mapped Combat Art rows have `-1`; rows `421` and `431` have non-`-1` values, but current-playthrough ownership semantics have not been verified.
- Human-readable skill point costs, prerequisite skills, Esoteric Text requirements, and direct boss/vendor sources have been added as acquisition metadata.
- Acquisition metadata is source-backed community guidance and marked `Probable`. It is not used as ownership evidence.

| Skill | Tree | Type | SkillParam row | SkillDescriptionId | EquipParamWeapon row | Weapon ID hex | State in S0000 | Status |
|---|---|---|---:|---:|---:|---|---|---|
| Whirlwind Slash | Shinobi Arts | Combat Art | 10 | 210000 | 5100 | `EC130000` | present at `0x8f990` | unlocked |
| Shadowrush | Shinobi Arts | Combat Art | 20 | 211000 | 6000 | `70170000` | absent | missing |
| Nightjar Slash | Prosthetic Arts | Combat Art | 110 | 310000 | 5200 | `50140000` | present at `0x8fac0` | unlocked |
| Nightjar Slash Reversal | Prosthetic Arts | Combat Art | 111 | 310100 | 7000 | `581B0000` | absent | missing |
| Ichimonji | Ashina Arts | Combat Art | 210 | 410000 | 5300 | `B4140000` | present at `0x8fb80` | unlocked |
| Ichimonji: Double | Ashina Arts | Combat Art | 211 | 410100 | 7100 | `BC1B0000` | present at `0x8fe60` | unlocked |
| Ashina Cross | Ashina Arts | Combat Art | 220 | 411000 | 5500 | `7C150000` | absent | missing |
| Praying Strikes | Temple Arts | Combat Art | 310 | 510000 | 5900 | `0C170000` | present at `0x8ffe0` | unlocked |
| Praying Strikes - Exorcism | Temple Arts | Combat Art | 311 | 510100 | 7500 | `4C1D0000` | absent | missing |
| Senpou Leaping Kicks | Temple Arts | Combat Art | 320 | 511000 | 5800 | `A8160000` | absent | missing |
| High Monk | Temple Arts | Combat Art | 321 | 511100 | 7400 | `E81C0000` | absent | missing |
| Shadowfall | Mushin Arts | Combat Art | 411 | 610100 | 7600 | `B01D0000` | absent | missing |
| Spiral Cloud Passage | Mushin Arts | Combat Art | 421 | 611100 | 7200 | `201C0000` | absent | missing |
| Empowered Mortal Draw | Mushin Arts | Combat Art | 431 | 612100 | 7300 | `841C0000` | absent | missing |
| Mortal Draw | Special Combat Arts | Combat Art | 630 | 670000 | 5700 | `44160000` | present at `0x8fd90` | unlocked |
| Dragon Flash | Special Combat Arts | Combat Art | 640 | 671000 | 5400 | `18150000` | absent | missing |
| Floating Passage | Special Combat Arts | Combat Art | 650 | 672000 | 5600 | `E0150000` | absent | missing |
| One Mind | Special Combat Arts | Combat Art | 660 | 673000 | 6100 | `D4170000` | absent | missing |

How it was verified:
- Read `SkillParam.csv` from `sekiro-online/params` and identified Combat Art rows where `Unk1` links to a Combat Art `EquipParamWeapon` row.
- Read `EquipParamWeapon.csv` from `sekiro-online/params` and used the named weapon rows to avoid promoting blank or unresolved rows.
- Scanned `USER_DATA000` in `S0000.sl2` for each little-endian Combat Art weapon row ID using the established weapon inventory record shape: item ID, quantity `1`, and the observed `80 80` prefix.
- Added automated parser tests requiring every mapped Combat Art to resolve through `inventory_weapon` evidence, with exact offsets for every present record and zero records for every missing record.
- Confirmed `SkillParam.EventFlagId` is not a complete ownership signal for this batch, so it remains research-only until semantics are verified.

Evidence/source:
- `data/sekiro/skills.json`
- `S0000.sl2` SHA-256 `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`
- sekiro-online `SkillParam.csv`: https://github.com/sekiro-online/params/blob/master/src/SkillParam.csv
- sekiro-online `EquipParamWeapon.csv`: https://github.com/sekiro-online/params/blob/master/src/EquipParamWeapon.csv
- Fextralife Skills and Skill Trees page, used for community skill tree/name/cost/prerequisite context: https://sekiroshadowsdietwice.wiki.fextralife.com/Skills+and+Skill+Trees
- `research/reports/exact_location_report.json`

Confidence: Verified for the mapped Combat Art param row links, named weapon rows, weapon IDs, and current save unlocked/missing states. Probable for acquisition metadata sourced from community skill/tree pages. Verified for Ninjutsu acquisition state. Unknown for in-save skill-tree text state, exact param-level cost/prerequisite semantics, and Sakura Dance row `670` / weapon row `7700`.

## Non-Combat-Art Skill Evidence

What was discovered:
- `SkillParam.SkillDescriptionId` lines up with named `EquipParamWeapon` rows for many non-Combat-Art Skills: martial arts, latent skills, and special skills.
- These named rows use the same save ownership shape already verified for Combat Arts and Prosthetic Tools: little-endian row ID in `USER_DATA000`, quantity `1`, and the observed `80 80` inventory prefix.
- In `S0000.sl2`, this verifies 23 additional unlocked Skills and 13 additional missing Skills.
- Absence is only promoted to `missing` for these rows because the row identity and weapon-record ownership shape are verified. Acquisition metadata and prerequisite rows are not used for status.

| Skill | Tree/source | Type | SkillParam row | SkillDescriptionId / weapon row | Weapon ID hex | State in S0000 | Status |
|---|---|---|---:|---:|---|---|---|
| Mid-air Deflection | Shinobi Arts | Martial Art | 2 | 200100 | `A40D0300` | present at `0x8fb20` | unlocked |
| Mikiri Counter | Shinobi Arts | Martial Art | 4 | 200300 | `6C0E0300` | present at `0x8f9f0` | unlocked |
| Run and Slide | Shinobi Arts | Martial Art | 5 | 200400 | `D00E0300` | present at `0x8fa40` | unlocked |
| Mid-air Combat Arts | Shinobi Arts | Martial Art | 6 | 200500 | `340F0300` | present at `0x8fb10` | unlocked |
| Vault Over | Shinobi Arts | Martial Art | 7 | 200600 | `980F0300` | absent | missing |
| Suppress Presence | Shinobi Arts | Latent Skill | 60 | 620000 | `E0750900` | present at `0x8f880` | unlocked |
| Suppress Sound | Shinobi Arts | Latent Skill | 61 | 620100 | `44760900` | absent | missing |
| Shinobi Eyes | Shinobi Arts | Latent Skill | 70 | 660400 | `B0130A00` | present at `0x8fa30` | unlocked |
| A Shinobi's Karma: Body | Shinobi Arts | Latent Skill | 75 | 650000 | `10EB0900` | present at `0x8fb30` | unlocked |
| A Shinobi's Karma: Mind | Shinobi Arts | Latent Skill | 76 | 650100 | `74EB0900` | absent | missing |
| Breath of Life: Light | Shinobi Arts | Latent Skill | 80 | 660000 | `20120A00` | present at `0x8ff60` | unlocked |
| Chasing Slice | Prosthetic Arts | Martial Art | 100 | 301000 | `C8970400` | present at `0x8f9d0` | unlocked |
| Fang and Blade | Prosthetic Arts | Martial Art | 101 | 301100 | `2C980400` | absent | missing |
| Projected Force | Prosthetic Arts | Martial Art | 102 | 301200 | `90980400` | absent | missing |
| Living Force | Prosthetic Arts | Martial Art | 103 | 301300 | `F4980400` | absent | missing |
| Grappling Hook Attack | Prosthetic Arts | Martial Art | 104 | 200000 | `400D0300` | present at `0x8faa0` | unlocked |
| Mid-air Prosthetic Tool | Prosthetic Arts | Martial Art | 105 | 200200 | `080E0300` | present at `0x8fa60` | unlocked |
| Emma's Medicine: Potency | Prosthetic Arts | Latent Skill | 170 | 640000 | `00C40900` | present at `0x8fd40` | unlocked |
| Emma's Medicine: Aroma | Prosthetic Arts | Latent Skill | 171 | 640100 | `64C40900` | present at `0x8fdb0` | unlocked |
| Sculptor's Karma: Blood | Prosthetic Arts | Latent Skill | 175 | 650200 | `D8EB0900` | absent | missing |
| Sculptor's Karma: Scars | Prosthetic Arts | Latent Skill | 176 | 650300 | `3CEC0900` | absent | missing |
| Breath of Nature: Light | Ashina Arts | Latent Skill | 265 | 660200 | `E8120A00` | present at `0x8fcf0` | unlocked |
| Ascending Carp | Ashina Arts | Latent Skill | 270 | 660600 | `78140A00` | present at `0x8fca0` | unlocked |
| Descending Carp | Ashina Arts | Latent Skill | 275 | 660700 | `DC140A00` | present at `0x8fbe0` | unlocked |
| Flowing Water | Ashina Arts | Latent Skill | 280 | 660800 | `40150A00` | present at `0x8fef0` | unlocked |
| Virtuous Deed | Temple Arts | Latent Skill | 365 | 630000 | `F09C0900` | absent | missing |
| Most Virtuous Deed | Temple Arts | Latent Skill | 366 | 630100 | `549D0900` | absent | missing |
| Devotion | Temple Arts | Latent Skill | 370 | 660500 | `14140A00` | absent | missing |
| Shinobi Medicine Rank 1 | Special Skills | Latent Skill | 600 | 640200 | `C8C40900` | present at `0x8f940` | unlocked |
| Shinobi Medicine Rank 2 | Special Skills | Latent Skill | 601 | 640300 | `2CC50900` | present at `0x8faf0` | unlocked |
| Shinobi Medicine Rank 3 | Special Skills | Latent Skill | 602 | 640400 | `90C50900` | present at `0x8ffc0` | unlocked |
| A Beast's Karma | Special Skills | Latent Skill | 603 | 650400 | `A0EC0900` | absent | missing |
| Breath of Life: Shadow | Special Skills | Latent Skill | 604 | 660100 | `84120A00` | present at `0x8feb0` | unlocked |
| Breath of Nature: Shadow | Special Skills | Latent Skill | 605 | 660300 | `4C130A00` | present at `0x8fd20` | unlocked |
| Mibu Breathing Technique | Special Skills | Special Skill | 610 | 680000 | `40600A00` | present at `0x8fdc0` | unlocked |
| Anti-air Deathblow | Special Skills | Special Skill | 620 | 681000 | `28640A00` | absent | missing |

How it was verified:
- Read `SkillParam.csv` and matched non-upgrade rows by `SkillDescriptionId`.
- Read `EquipParamWeapon.csv` and kept only rows with translated names matching the Skill description row.
- Scanned `USER_DATA000` in `S0000.sl2` for each little-endian row ID using the verified `inventory_weapon` record shape.
- Added automated tests for every newly mapped non-Combat-Art Skill, including exact offsets for present records and zero records for missing records.

Evidence/source:
- `data/sekiro/skills.json`
- `S0000.sl2` SHA-256 `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`
- sekiro-online `SkillParam.csv`: https://github.com/sekiro-online/params/blob/master/src/SkillParam.csv
- sekiro-online `EquipParamWeapon.csv`: https://github.com/sekiro-online/params/blob/master/src/EquipParamWeapon.csv
- `research/reports/exact_location_report.json`

Confidence: Verified for row identity, weapon ID hex values, and current save unlocked/missing states. Unknown for non-Combat-Art acquisition costs, prerequisite metadata, and tree unlock-state semantics.

## Ninjutsu State

What was discovered:
- `EquipParamGoods.csv` identifies goods rows `2100` Bloodsmoke, `2110` Puppeteer, and `2120` Bestowal Ninjutsu.
- `ItemLotParam.csv` maps those rewards to persistent acquisition flags `6745`, `6746`, and `6747`.
- Ninjutsu status is `unlocked` when its acquisition flag is ON, `missing` when OFF, and `unknown` only when the flag cannot be decoded.
- The reference and After Divine Dragon fixtures have Bloodsmoke and Puppeteer unlocked with Bestowal missing. The Before Isshin fixture has all three unlocked.

How it was verified:
- Cross-checked the three ItemLot rows, goods IDs, and `getItemFlagId` values.
- Read the flags through the verified serialized event-flag decoder in all three sanitized fixtures.
- Added regression assertions for the exact Ninjutsu state in each fixture.

Evidence/source:
- sekiro-online `EquipParamGoods.csv`: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- sekiro-online `ItemLotParam.csv`: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- `data/sekiro/skills.json`
- `packages/analyzer/test/sekiro-golden.test.ts`
- `research/fixtures/README.md`

Confidence: Verified for Ninjutsu acquisition state across all three fixtures.
## Acquisition Metadata

What was discovered:
- Every mapped Combat Art now has an `acquisitionMetadata` block in `data/sekiro/skills.json`.
- Missing skills in the current report carry user-facing guidance: skill tree, acquisition method, skill point cost where applicable, prerequisite skill names, Esoteric Text requirement, and direct vendor/boss/source where applicable.
- `requiredSkillPoints` and `prerequisites.skills[]` are populated from community skill-tree tables. These fields are guidance only and are not read by status logic.
- Direct special Combat Arts use `skillPointCostType = not_applicable_direct_acquisition`.
- Esoteric Text ownership is not used to infer whether any skill is unlocked.

| Skill | Tree/source | Cost | Prerequisites/source | Text or direct acquisition | Metadata confidence |
|---|---|---:|---|---|---|
| Whirlwind Slash | Shinobi Arts | 1 | none listed | Shinobi Esoteric Text from Sculptor after at least 1 skill point | Probable |
| Shadowrush | Shinobi Arts | 6 | Shinobi Eyes; Mid-air Combat Arts | Shinobi Esoteric Text from Sculptor after at least 1 skill point | Probable |
| Nightjar Slash | Prosthetic Arts | 2 | Grappling Hook Attack | Prosthetic Esoteric Text from Sculptor after fitting any three Prosthetic Tools | Probable |
| Nightjar Slash Reversal | Prosthetic Arts | 3 | Nightjar Slash; Emma's Medicine: Potency | Prosthetic Esoteric Text from Sculptor after fitting any three Prosthetic Tools | Probable |
| Ichimonji | Ashina Arts | 2 | none listed | Ashina Esoteric Text from Tengu's rat quest; later Isshin tower fallback | Probable |
| Ichimonji: Double | Ashina Arts | 3 | Ascending Carp; Descending Carp | Ashina Esoteric Text from Tengu's rat quest; later Isshin tower fallback | Probable |
| Ashina Cross | Ashina Arts | 5 | Flowing Water; Ichimonji: Double | Ashina Esoteric Text from Tengu's rat quest; later Isshin tower fallback | Probable |
| Praying Strikes | Temple Arts | 2 | none listed | Senpou Esoteric Text in small shrine near Main Hall Idol | Probable |
| Praying Strikes - Exorcism | Temple Arts | 3 | Praying Strikes | Senpou Esoteric Text in small shrine near Main Hall Idol | Probable |
| Senpou Leaping Kicks | Temple Arts | 3 | Virtuous Deed | Senpou Esoteric Text in small shrine near Main Hall Idol | Probable |
| High Monk | Temple Arts | 4 | Senpou Leaping Kicks | Senpou Esoteric Text in small shrine near Main Hall Idol | Probable |
| Shadowfall | Mushin Arts | 6 | High Monk; Shadowrush | Mushin Esoteric Text from Tengu at Great Serpent Shrine; later Emma fallback | Probable |
| Spiral Cloud Passage | Mushin Arts | 9 | Shadowrush; Ashina Cross | Mushin Esoteric Text from Tengu at Great Serpent Shrine; later Emma fallback | Probable |
| Empowered Mortal Draw | Mushin Arts | 5 | Living Force; Ashina Cross | Mushin Esoteric Text from Tengu at Great Serpent Shrine; later Emma fallback | Probable |
| Mortal Draw | Special Combat Arts | n/a | none listed | Mortal Blade from Divine Child after Folding Screen Monkeys | Probable |
| Dragon Flash | Special Combat Arts | n/a | none listed | Defeat Isshin, The Sword Saint after choosing to Break the Iron Code | Probable |
| Floating Passage | Special Combat Arts | n/a | none listed | Buy Floating Passage Text from Pot Noble Harunaga for 5 Treasure Carp Scales | Probable |
| One Mind | Special Combat Arts | n/a | none listed | Defeat Isshin Ashina after choosing to Obey the Iron Code | Probable |

How it was verified:
- Parsed the Fextralife Skills and Skill Trees table rows for the 18 mapped Combat Arts.
- Read the individual Esoteric Text pages for Shinobi, Prosthetic, Ashina, Senpou, and Mushin text acquisition routes.
- Read individual pages for Mortal Draw, Dragon Flash, Floating Passage, and One Mind to source direct acquisition routes.
- Added automated tests asserting acquisition metadata for every mapped skill and specific missing-skill guidance for `shadowrush`, `floating_passage`, `dragon_flash`, and `one_mind`.
- Confirmed tests still require status to come from `inventory_weapon` evidence, not from prerequisites, text ownership, bosses, vendors, or acquisition metadata.

Evidence/source:
- Fextralife Skills and Skill Trees: https://sekiroshadowsdietwice.wiki.fextralife.com/Skills+and+Skill+Trees
- Shinobi Esoteric Text: https://sekiroshadowsdietwice.wiki.fextralife.com/Shinobi+Esoteric+Text
- Prosthetic Esoteric Text: https://sekiroshadowsdietwice.wiki.fextralife.com/Prosthetic+Esoteric+Text
- Ashina Esoteric Text: https://sekiroshadowsdietwice.wiki.fextralife.com/Ashina+Esoteric+Text
- Senpou Esoteric Text: https://sekiroshadowsdietwice.wiki.fextralife.com/Senpou+Esoteric+Text
- Mushin Esoteric Text: https://sekiroshadowsdietwice.wiki.fextralife.com/Mushin+Esoteric+Text
- Mortal Draw: https://sekiroshadowsdietwice.wiki.fextralife.com/Mortal+Draw
- Dragon Flash: https://sekiroshadowsdietwice.wiki.fextralife.com/Dragon+Flash
- Floating Passage: https://sekiroshadowsdietwice.wiki.fextralife.com/Floating+Passage
- One Mind: https://sekiroshadowsdietwice.wiki.fextralife.com/One+Mind

Confidence: Probable for acquisition metadata because it is community-guide backed and not independently verified from save data. Verified status uses direct `inventory_weapon` evidence for mapped weapon-backed Skills and persistent ItemLot acquisition flags for Ninjutsu.

## Unresolved Skill Coverage

What remains unresolved:
- `SkillParam` row `670` appears to link to weapon row `7700`; the inspected public `EquipParamWeapon` row name is blank, so Sakura Dance has not been promoted into the verified mapping.
- Exact param-level semantics for skill point costs, prerequisite fields, and skill-tree text state remain unresolved. Those fields remain acquisition guidance and never drive ownership.

Ninjutsu ownership is no longer part of unresolved coverage; its persistent acquisition flags are verified and regression-tested.

Evidence/source:
- sekiro-online `SkillParam.csv`: https://github.com/sekiro-online/params/blob/master/src/SkillParam.csv
- sekiro-online `EquipParamWeapon.csv`: https://github.com/sekiro-online/params/blob/master/src/EquipParamWeapon.csv
- `data/sekiro/skills.json`

Confidence: Verified for the current mapped Skills and Ninjutsu statuses. Unknown for Sakura Dance row `670` and exact param semantics behind guidance metadata.