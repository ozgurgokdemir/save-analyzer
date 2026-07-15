# Event Flags Research

Last updated: 2026-07-08

## Event flag storage

What was discovered:
- Mapped event flags are readable from `USER_DATA000` at base offset `0xE8000`.
- Formula for currently verified flags: `slot[0xE8000 + floor((eventFlag % 1000000) / 8)]`, bit `((eventFlag % 1000000) % 8)`.
- Bit order is LSB-first.

How it was verified:
- The seven non-shop Gourd Seed item-lot flags from SoulSplitter produce exactly six collected non-shop seeds and one missing non-shop seed in the provided save.
- ShopLineupParam flags `71101210` and `71102000` resolve the two merchant Gourd Seeds and reconcile with the inventory-derived total of 7/9 Gourd Seeds.
- The 40 primary Prayer Bead pickup/shop flags are readable with the same layout, but their ON/OFF count does not reconcile with the inventory-derived carried Prayer Bead total in this save.
- Eleven verified secondary Prayer Bead ItemLotParam flags are ON in this save and reconcile the 26 inventory-derived beads against the 15 ON primary flags.
- Thirteen additional paired secondary Prayer Bead ItemLotParam flags are OFF, and the Abandoned Dungeon Memorial Mob shop flag is OFF.
- The remaining Prayer Bead OFF primary flags are now modeled as missing by evidence only where the verified missing-evidence rule is satisfied.

Evidence/source:
- `data/sekiro/event-flag-layout.json`
- `S0000.sl2` SHA-256 `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`
- SoulSplitter Sekiro item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- `research/reports/exact_location_report.json`

Confidence: Verified for the mapped low item flags, Prayer Bead primary flag states, 24 secondary Prayer Bead item-lot flags, Prayer Bead shop flag, boss Memory award flag states, and candidate SoulSplitter boss split flag states in this save. Unknown for boss-defeat semantics, SoulSplitter `930x` persistent completion semantics, and Offering Box semantics.

## SkillParam EventFlagId field

What was discovered:
- `SkillParam.csv` includes an `EventFlagId` field, but it is not a verified universal skill ownership signal.
- Most verified Combat Art rows in the current Skills batch have `EventFlagId = -1`.
- `Spiral Cloud Passage` row `421` and `Empowered Mortal Draw` row `431` have non-`-1` values, but those flag semantics have not been verified as current-save ownership state.
- The Skills analyzer therefore uses verified `inventory_weapon` evidence for mapped Combat Arts and does not read `SkillParam.EventFlagId` for skill status yet.

How it was verified:
- Inspected `SkillParam.csv` from `sekiro-online/params` while building `data/sekiro/skills.json`.
- Compared the field coverage against mapped Combat Art rows and avoided using incomplete or semantically unresolved flags in status logic.

Evidence/source:
- `data/sekiro/skills.json`
- sekiro-online `SkillParam.csv`: https://github.com/sekiro-online/params/blob/master/src/SkillParam.csv

Confidence: Verified that the field exists and is incomplete for the mapped Combat Art subset. Unknown for any future row-specific ownership semantics.

## Verified low event flag states in S0000

What was discovered:

| Event flag | Meaning in current data | State in S0000 | Confidence |
|---:|---|---|---|
| 6723 | General Naomori Kawarada Gourd Seed drop | ON | Verified |
| 6724 | Sunken Valley Gourd Seed treasure | OFF | Verified |
| 6725 | Building after Chained Ogre Gourd Seed | ON | Verified |
| 6726 | Upper Tower Antechamber Gourd Seed chest | ON | Verified |
| 6727 | Senpou Temple Gourd Seed treasure | ON | Verified |
| 6728 | Mibu Village Gourd Seed treasure | ON | Verified |
| 6729 | Fountainhead Palace Gourd Seed chest | ON | Verified |
| 6760 | General Naomori Kawarada Prayer Bead | OFF | Verified |
| 6761 | Chained Ogre Prayer Bead | ON | Verified |
| 6762 | General Tenzen Yamauchi Prayer Bead | ON | Verified |
| 6763 | Shinobi Hunter Enshin of Misen Prayer Bead | OFF | Verified |
| 6764 | Juzou the Drunkard Prayer Bead | ON | Verified |
| 6765 | Blazing Bull Prayer Bead | OFF | Verified |
| 6766 | General Kuranosuke Matsumoto Prayer Bead | OFF | Verified |
| 6767 | Ashina Elite - Jinsuke Saze Prayer Bead | ON | Verified |
| 6769 | Seven Ashina Spears - Shikibu Toshikatsu Yamauchi Prayer Bead | OFF | Verified |
| 6770 | Lone Shadow Longswordsman Prayer Bead | ON | Verified |
| 6771 | Armored Warrior Prayer Bead | ON | Verified |
| 6772 | Long-arm Centipede Sen'un Prayer Bead | OFF | Verified |
| 6773 | Snake Eyes Shirafuji Prayer Bead | OFF | Verified |
| 6774 | Long-arm Centipede Giraffe Prayer Bead | ON | Verified |
| 6775 | Snake Eyes Shirahagi Prayer Bead | ON | Verified |
| 6776 | Tokujiro the Glutton Prayer Bead | OFF | Verified |
| 6777 | O'Rin of the Water Prayer Bead | OFF | Verified |
| 6778 | Chained Ogre Ashina Castle Prayer Bead | ON | Verified |
| 6779 | Lone Shadow Vilehand Prayer Bead | ON | Verified |
| 6780 | Lone Shadow Masanaga the Spear-Bearer Prayer Bead | ON | Verified |
| 6781 | Lone Shadow Masanaga the Spear-Bearer Hirata Revisit Prayer Bead | ON | Verified |
| 6782 | Juzou the Drunkard Hirata Revisit Prayer Bead | OFF | Verified |
| 6783 | Sakura Bull of the Palace Prayer Bead | ON | Verified |
| 6784 | Okami Leader Shizu Prayer Bead | OFF | Verified |
| 6785 | Ashina Elite - Ujinari Mizou Prayer Bead | OFF | Verified |
| 6786 | Seven Ashina Spears - Shume Masaji Oniwa Prayer Bead | OFF | Verified |
| 6787 | Shigekichi of the Red Guard Prayer Bead | OFF | Verified |
| 6788 | Ashina Castle Gate attic Prayer Bead | ON | Verified |
| 6789 | Hirata Audience Chamber hidden wall Prayer Bead | OFF | Verified |
| 6790 | Ashina Castle hidden wall chest Prayer Bead | ON | Verified |
| 6791 | Senpou Temple underwater Prayer Bead | OFF | Verified |
| 6792 | Sunken Valley Prayer Bead sample 1 | OFF | Verified |
| 6793 | Sunken Valley Prayer Bead sample 2 | OFF | Verified |
| 6794 | Sunken Valley Prayer Bead sample 3 | OFF | Verified |
| 6795 | Watermill attic Prayer Bead | OFF | Verified |
| 6796 | Mibu underwater chest Prayer Bead | OFF | Verified |
| 6797 | Fountainhead lake chest Prayer Bead | OFF | Verified |
| 6798 | Headless Ape Prayer Bead 1 | OFF | Verified |
| 6799 | Headless Ape Prayer Bead 2 | OFF | Verified |
| 71101210 | Battlefield Memorial Mob Gourd Seed purchase | ON | Verified |
| 71102000 | Fujioka the Info Broker Gourd Seed purchase | OFF | Verified |
| 71111000 | Abandoned Dungeon Memorial Mob Prayer Bead purchase | OFF | Verified |

How it was verified:
- Read all listed flags through the documented `0xE8000` event flag layout.
- Mapped rows are stored in `data/sekiro/gourd-seeds.json` and `data/sekiro/prayer-beads.json`.
- Prayer Bead flags were added from SoulSplitter item pickup rows and cross-checked against the PowerPyx Prayer Bead guide before being read from `S0000.sl2`.
- The Abandoned Dungeon Memorial Mob Prayer Bead shop flag was added from public ShopLineupParam row data.

Evidence/source:
- `research/reports/exact_location_report.json`
- SoulSplitter item pickup flag rows.

Confidence: Verified for this save

## Boss Memory award flags

What was discovered:
- Boss Memory award flags are readable through the same `0xE8000` event flag layout.
- Memory award flags are comparison evidence only; they are not treated as verified `defeated` boss evidence.
- Manual fixture-playthrough verification establishes that `isshin_ashina` was not defeated in this first-playthrough save despite its Memory award flag reading ON.
- Manual fixture-playthrough verification establishes that `genichiro` was defeated, but candidate SoulSplitter flag `9303` reads OFF.
- `headless_ape` is uncertain; candidate SoulSplitter flag `9307` reads ON.
- All boss statuses are therefore `unknown` until a verified boss defeat/progression flag is mapped.

| Event flag | ItemLot row | Boss Memory | State in S0000 | Parser status |
|---:|---:|---|---|---|
| 50002001 | 2001 | Gyoubu Oniwa | ON | unknown |
| 50002011 | 2011 | Guardian Ape | ON | unknown |
| 50002017 | 2017 | Headless Ape | ON | unknown |
| 50002021 | 2021 | Folding Screen Monkeys | ON | unknown |
| 50002031 | 2031 | Lady Butterfly | ON | unknown |
| 50002041 | 2041 | Demon of Hatred | ON | unknown |
| 50002051 | 2051 | Corrupted Monk | ON | unknown |
| 50002061 | 2061 | True Monk | OFF | unknown |
| 50002071 | 2071 | Divine Dragon | OFF | unknown |
| 50002081 | 2081 | Genichiro | ON | unknown |
| 50002091 | 2091 | Great Shinobi Owl | ON | unknown |
| 50002101 | 2101 | Owl (Father) | ON | unknown |
| 50002121 | 2121 | Isshin Ashina | ON | unknown |
| 50002131 | 2131 | Sword Saint Isshin | ON | unknown |

How it was verified:
- Public ItemLotParam row data maps each Memory award row to its `getItemFlagId`.
- Public EquipParamGoods row data maps goods IDs `5200` through `5213` to boss Memory names.
- The parser reads the listed flags from `USER_DATA000`.

Evidence/source:
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- `data/sekiro/bosses.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save's event flag states only. Unknown for boss defeated/not-defeated status.

## Candidate SoulSplitter boss split flags

What was discovered:
- SoulSplitter maps Sekiro boss split enum values `9301` through `9317` in `src/SoulMemory/Sekiro/Boss.cs`.
- SoulSplitter's Sekiro split model stores Boss split values as `Flag`, and `SekiroSplitter` reads them via `ReadEventFlag`.
- The current parser records these as `speedrunSplitFlagCandidate` evidence only.
- These are not verified current-cycle boss defeated flags, and they do not change boss status.
- Manual fixture-playthrough verification establishes that `genichiro` was defeated; candidate flag `9303` reads OFF in `S0000.sl2`.
- Manual fixture-playthrough verification establishes that `isshin_ashina` has not been defeated; candidate flag `9316` reads OFF in `S0000.sl2`.
- The earlier `headless_ape` negative is no longer treated as verified; candidate flag `9307` reads ON.
- Therefore SoulSplitter `930x` candidate split flags are not treated as reliable persistent boss-completion evidence, whether ON or OFF.

| Event flag | Boss | State in S0000 | Parser status contribution |
|---:|---|---|---|
| 9301 | Gyoubu Oniwa | ON | candidate only |
| 9302 | Lady Butterfly | ON | candidate only |
| 9303 | Genichiro | OFF | candidate only |
| 9304 | Guardian Ape | ON | candidate only |
| 9305 | Folding Screen Monkeys | ON | candidate only |
| 9306 | Corrupted Monk | ON | candidate only |
| 9307 | Headless Ape | ON | candidate only |
| 9308 | Great Shinobi Owl | ON | candidate only |
| 9309 | True Monk | ON | candidate only |
| 9310 | Divine Dragon | ON | candidate only |
| 9312 | Sword Saint Isshin | OFF | candidate only |
| 9313 | Demon of Hatred | ON | candidate only |
| 9316 | Isshin Ashina | OFF | candidate only |
| 9317 | Owl (Father) | ON | candidate only |

How it was verified:
- Read SoulSplitter source for Boss enum values and split logic.
- Read the candidate flags from `USER_DATA000` using the documented `0xE8000` event flag layout.
- Added parser tests that assert these flags are present as evidence and that they do not produce `defeated` or `not_defeated` status.

Evidence/source:
- SoulSplitter Boss enum: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulMemory/Sekiro/Boss.cs
- SoulSplitter split model: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulSplitter/Splits/Sekiro/Split.cs
- SoulSplitter splitter logic: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulSplitter/Splitters/SekiroSplitter.cs
- `data/sekiro/bosses.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for candidate flag state reads in this save. Unknown for persistent save boss defeated/not-defeated semantics.

## Secondary Prayer Bead item-lot flags

What was discovered:
- These 11 secondary ItemLotParam event flags are ON in `S0000.sl2`.
- Each flag belongs to a verified secondary reward/replacement row paired with an OFF primary Prayer Bead flag.
- The 11 ON secondary flags reconcile the save's 26 inventory/progression-derived Prayer Beads with the 15 ON primary Prayer Bead flags.

| Event flag | Row ID | Primary Prayer Bead location | State in S0000 | Confidence |
|---:|---:|---|---|---|
| 51100905 | 10200005 | General Naomori Kawarada Prayer Bead | ON | Verified |
| 51110970 | 10202005 | General Kuranosuke Matsumoto Prayer Bead | ON | Verified |
| 51701015 | 11900005 | Snake Eyes Shirafuji Prayer Bead | ON | Verified |
| 51500935 | 10702005 | Tokujiro the Glutton Prayer Bead | ON | Verified |
| 51500925 | 70000005 | O'Rin of the Water Prayer Bead | ON | Verified |
| 52500905 | 13100005 | Okami Leader Shizu Prayer Bead | ON | Verified |
| 51110978 | 14001005 | Ashina Elite - Ujinari Mizou Prayer Bead | ON | Verified |
| 51110976 | 13700005 | Blazing Bull Prayer Bead | ON | Verified |
| 50002017 | 2017 | Headless Ape Prayer Bead 1 | ON | Verified |
| 51500045 | 1500045 | Watermill attic Prayer Bead | ON | Verified |
| 51700025 | 1700025 | Sunken Valley treasure Prayer Bead 1 | ON | Verified |

How it was verified:
- SoulSplitter provides the row-to-event-flag mappings.
- Public `ItemLotParam.csv` confirms each secondary row's `getItemFlagId`.
- The parser reads the flags from `USER_DATA000` through the documented `0xE8000` event flag layout.
- Automated tests assert these exact flags are present in `eventFlags.mappedStates` and ON.

Evidence/source:
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- sekiro-online ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- `data/sekiro/prayer-beads.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save

## Missing-evidence Prayer Bead flags

What was discovered:
- These secondary ItemLotParam flags are OFF in `S0000.sl2`.
- Each OFF secondary flag is paired with an OFF primary Prayer Bead item-lot flag that awards item ID `4000`.
- Together with the OFF Abandoned Dungeon Memorial Mob shop purchase flag, these support `missingByEvidence = 14`.

| Event flag | Row ID | Prayer Bead location | State in S0000 | Confidence |
|---:|---:|---|---|---|
| 51000925 | 10500005 | Shinobi Hunter Enshin of Misen Prayer Bead | OFF | Verified |
| 51112900 | 10212005 | Seven Ashina Spears - Shikibu Toshikatsu Yamauchi Prayer Bead | OFF | Verified |
| 52000945 | 10400005 | Long-arm Centipede Sen'un Prayer Bead | OFF | Verified |
| 51500325 | 1500325 | Mibu Village underwater chest Prayer Bead | OFF | Verified |
| 52500025 | 2500025 | Fountainhead Palace lake chest Prayer Bead | OFF | Verified |
| 51700035 | 1700035 | Sunken Valley treasure Prayer Bead 2 | OFF | Verified |
| 51700045 | 1700045 | Sunken Valley treasure Prayer Bead 3 | OFF | Verified |
| 51000505 | 1000505 | Hirata Audience Chamber hidden wall Prayer Bead | OFF | Verified |
| 52000045 | 2000045 | Senpou Temple underwater Prayer Bead | OFF | Verified |
| 50002018 | 2018 | Headless Ape Prayer Bead 2 | OFF | Verified |
| 51000955 | 10700105 | Juzou the Drunkard Hirata Revisit Prayer Bead | OFF | Verified |
| 51112910 | 10212105 | Seven Ashina Spears - Shume Masaji Oniwa Prayer Bead | OFF | Verified |
| 51100965 | 10701005 | Shigekichi of the Red Guard Prayer Bead | OFF | Verified |
| 71111000 | 1110000 | Abandoned Dungeon Memorial Mob Prayer Bead shop purchase | OFF | Verified |

How it was verified:
- Public ItemLotParam row data confirms the secondary rows and their `getItemFlagId` values.
- Public ShopLineupParam row data confirms shop row `1110000` and EventFlag `71111000`.
- The parser reads each flag from `USER_DATA000` through the documented event flag layout.

Evidence/source:
- sekiro-online ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- sekiro-online ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv
- `data/sekiro/prayer-beads.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save

## Shop purchase flags

What was discovered:
- Gourd Seed shop purchase state is resolved for `S0000.sl2`.
- SoulsMods Paramdex confirms `ShopLineupParam` has `eventFlag` and `flagId_forRelease` fields.
- Public ShopLineupParam row data maps:
  - Battlefield Memorial Mob row `1100101` to event flag `71101210`.
  - Fujioka row `1100400` to event flag `71102000`.
  - Abandoned Dungeon Memorial Mob Prayer Bead row `1110000` to event flag `71111000`.
- In `S0000.sl2`, flag `71101210` is ON and flag `71102000` is OFF.
- In `S0000.sl2`, flag `71111000` is OFF.
- The Abandoned Dungeon Memorial Mob Prayer Bead shop flag OFF state is now reported as missing by verified shop-purchase evidence after Prayer Bead reconciliation was solved.

How it was verified:
- Read Paramdex `ShopLineupParam.xml` field definitions.
- Read public ShopLineupParam row data from `sekiro-online/params`.
- Confirmed both rows sell equip ID `4400`, matching the verified Gourd Seed goods item ID.
- Confirmed row `1110000` sells equip ID `4000`, matching the verified Prayer Bead goods item ID.
- Read the merchant event flags from `USER_DATA000` using the verified last-six-digit event flag index.
- The resulting states reconcile exactly with the save's inventory-derived 7/9 Gourd Seed count.
- The Prayer Bead shop state is verified independently and now contributes to the reconciled 26 collected / 14 missing / 0 unknown Prayer Bead report.

Evidence/source:
- Paramdex repository: https://github.com/soulsmods/Paramdex
- `ShopLineupParam.xml`: https://github.com/soulsmods/Paramdex/blob/master/SDT/Defs/ShopLineupParam.xml
- ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv
- Local save scan performed on `S0000.sl2`

Confidence: Verified for the two Gourd Seed shop purchase flags and the Abandoned Dungeon Memorial Mob Prayer Bead shop purchase flag in this save
