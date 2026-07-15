# Item Lots Research

Last updated: 2026-07-07

## ItemLotParam flag source

What was discovered:
- SoulSplitter's Sekiro item pickup flag table maps ItemLotParam row IDs to event flags extracted via Yapped.
- `ItemLotParam` has `getItemFlagId` fields in Paramdex, matching the concept of item pickup flags.
- For Prayer Beads, these item-lot pickup/award flags are primary evidence signals, not complete aggregate collection truth in the current save.
- In `S0000.sl2`, 15 primary Prayer Bead pickup/shop flags are ON, 25 are OFF, and the inventory/progression-derived Prayer Bead total is 26 / 40.
- Eleven secondary ItemLotParam reward/replacement rows paired with OFF primary Prayer Bead rows have ON event flags in `S0000.sl2`.
- Thirteen more secondary ItemLotParam rows paired with OFF primary Prayer Bead rows have OFF event flags in `S0000.sl2`.
- Public ItemLotParam row data confirms these secondary rows award non-Prayer-Bead items and carry independent `getItemFlagId` values.

How it was verified:
- Compared SoulSplitter row/event flag mappings with low event flag states in `S0000.sl2`.
- Read SoulsMods Paramdex `ItemLotParam.xml` field definitions.
- Read public `sekiro-online/params` `ItemLotParam.csv` rows for the secondary reward/replacement rows.
- Regenerated the parser report and tests after adding Prayer Bead evidence signals; OFF primary Prayer Bead item-lot flags are only marked missing when paired verified missing evidence is also OFF.

Evidence/source:
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- Paramdex ItemLotParam definition: https://github.com/soulsmods/Paramdex/blob/master/SDT/Defs/ItemLotParam.xml
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- `research/reports/exact_location_report.json`

Confidence: Verified for primary rows currently in `data/sekiro`, the 11 secondary rows that reconcile collected locations in `S0000.sl2`, and the 13 secondary rows that support missing-by-evidence locations; Unknown for unmapped Offering Box and boss-defeat flags

## Verified Gourd Seed item-lot rows

| Row ID | Event flag | Entry | Confidence |
|---:|---:|---|---|
| 10200001 | 6723 | General Naomori Kawarada drop | Verified |
| 1100200 | 6725 | Building after Chained Ogre | Verified |
| 1110020 | 6726 | Upper Tower Antechamber chest | Verified |
| 2000730 | 6727 | Senpou Temple treasure | Verified |
| 1700820 | 6724 | Sunken Valley treasure | Verified |
| 1500010 | 6728 | Mibu Village glowing tree | Verified |
| 2500000 | 6729 | Palace Grounds chest | Verified |

How it was verified:
- Source rows are present in SoulSplitter's item pickup flag table.
- Save flag states are read successfully with the low event flag reader.

Evidence/source:
- `data/sekiro/gourd-seeds.json`
- `research/reports/exact_location_report.json`

Confidence: Verified

## Verified sampled Prayer Bead item-lot rows

| Row ID | Event flag | Entry | Confidence |
|---:|---:|---|---|
| 2015 | 6798 | Headless Ape Prayer Bead 1 | Verified |
| 2016 | 6799 | Headless Ape Prayer Bead 2 | Verified |
| 1000500 | 6789 | Hirata Audience Chamber hidden wall Prayer Bead | Verified |
| 1100310 | 6788 | Ashina Castle Gate attic Prayer Bead | Verified |
| 10200000 | 6760 | General Naomori Kawarada Prayer Bead | Verified |
| 50201000 | 6761 | Chained Ogre Prayer Bead | Verified |
| 10200100 | 6762 | General Tenzen Yamauchi Prayer Bead | Verified |
| 10500000 | 6763 | Shinobi Hunter Enshin of Misen Prayer Bead | Verified |
| 10700000 | 6764 | Juzou the Drunkard Prayer Bead | Verified |
| 13700000 | 6765 | Blazing Bull Prayer Bead | Verified |
| 10202000 | 6766 | General Kuranosuke Matsumoto Prayer Bead | Verified |
| 14000000 | 6767 | Ashina Elite - Jinsuke Saze Prayer Bead | Verified |
| 10212000 | 6769 | Seven Ashina Spears - Shikibu Toshikatsu Yamauchi Prayer Bead | Verified |
| 14702000 | 6770 | Lone Shadow Longswordsman Prayer Bead | Verified |
| 11300000 | 6771 | Armored Warrior Prayer Bead | Verified |
| 10400000 | 6772 | Long-arm Centipede Sen'un Prayer Bead | Verified |
| 11900000 | 6773 | Snake Eyes Shirafuji Prayer Bead | Verified |
| 10401100 | 6774 | Long-arm Centipede Giraffe Prayer Bead | Verified |
| 11901100 | 6775 | Snake Eyes Shirahagi Prayer Bead | Verified |
| 10702000 | 6776 | Tokujiro the Glutton Prayer Bead | Verified |
| 70000000 | 6777 | O'Rin of the Water Prayer Bead | Verified |
| 50200000 | 6778 | Chained Ogre Ashina Castle Prayer Bead | Verified |
| 14700000 | 6779 | Lone Shadow Vilehand Prayer Bead | Verified |
| 14701000 | 6780 | Lone Shadow Masanaga the Spear-Bearer Prayer Bead | Verified |
| 14703100 | 6781 | Lone Shadow Masanaga the Spear-Bearer Hirata Revisit Prayer Bead | Verified |
| 10700100 | 6782 | Juzou the Drunkard Hirata Revisit Prayer Bead | Verified |
| 13800000 | 6783 | Sakura Bull of the Palace Prayer Bead | Verified |
| 13100000 | 6784 | Okami Leader Shizu Prayer Bead | Verified |
| 14001000 | 6785 | Ashina Elite - Ujinari Mizou Prayer Bead | Verified |
| 10212100 | 6786 | Seven Ashina Spears - Shume Masaji Oniwa Prayer Bead | Verified |
| 10701000 | 6787 | Shigekichi of the Red Guard Prayer Bead | Verified |
| 1110170 | 6790 | Ashina Castle hidden wall chest Prayer Bead | Verified |
| 2000040 | 6791 | Senpou Temple underwater Prayer Bead | Verified |
| 1500320 | 6796 | Mibu Village underwater chest Prayer Bead | Verified |
| 1500040 | 6795 | Watermill attic Prayer Bead | Verified |
| 2500020 | 6797 | Fountainhead Palace lake chest Prayer Bead | Verified |
| 1700020 | 6792 | Sunken Valley treasure Prayer Bead 1 | Verified |
| 1700030 | 6793 | Sunken Valley treasure Prayer Bead 2 | Verified |
| 1700040 | 6794 | Sunken Valley treasure Prayer Bead 3 | Verified |

How it was verified:
- Source rows are present in SoulSplitter's item pickup flag table.
- Exact human-readable location names for the 2026-07-07 Prayer Bead batches were cross-checked against the PowerPyx Prayer Bead guide.
- Save flag states are read successfully with the documented event flag reader.
- Parser tests assert that these row/event mappings are retained as `itemLotFlag` evidence while OFF primary flags are not promoted to definitely missing exact locations.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- `research/reports/exact_location_report.json`
- PowerPyx Prayer Bead guide: https://www.powerpyx.com/sekiro-shadows-die-twice-all-prayer-bead-locations/

Confidence: Verified for these sampled row/event/location mappings only; Unknown for exact missing-location status when a mapped Prayer Bead item-lot flag is OFF

## Verified secondary Prayer Bead item-lot rows

What was discovered:
- Eleven secondary ItemLotParam rows explain the current save's 11 collected-but-unattributed Prayer Beads.
- The primary Prayer Bead item-lot flags for these locations are OFF, but the listed secondary row flags are ON.
- These secondary rows award non-Prayer-Bead item IDs, so they are modeled as reward/replacement attribution signals rather than duplicate Prayer Bead pickup rows.

| Primary location | Primary row | Primary flag | Secondary row | Secondary flag | Awarded item ID | State in S0000 | Confidence |
|---|---:|---:|---:|---:|---:|---|---|
| General Naomori Kawarada Prayer Bead | 10200000 | 6760 | 10200005 | 51100905 | 3704 | ON | Verified |
| General Kuranosuke Matsumoto Prayer Bead | 10202000 | 6766 | 10202005 | 51110970 | 3704 | ON | Verified |
| Snake Eyes Shirafuji Prayer Bead | 11900000 | 6773 | 11900005 | 51701015 | 3704 | ON | Verified |
| Tokujiro the Glutton Prayer Bead | 10702000 | 6776 | 10702005 | 51500935 | 3704 | ON | Verified |
| O'Rin of the Water Prayer Bead | 70000000 | 6777 | 70000005 | 51500925 | 3704 | ON | Verified |
| Okami Leader Shizu Prayer Bead | 13100000 | 6784 | 13100005 | 52500905 | 3704 | ON | Verified |
| Ashina Elite - Ujinari Mizou Prayer Bead | 14001000 | 6785 | 14001005 | 51110978 | 3704 | ON | Verified |
| Blazing Bull Prayer Bead | 13700000 | 6765 | 13700005 | 51110976 | 3704 | ON | Verified |
| Headless Ape Prayer Bead 1 | 2015 | 6798 | 2017 | 50002017 | 5213 | ON | Verified |
| Watermill attic Prayer Bead | 1500040 | 6795 | 1500045 | 51500045 | 3720 | ON | Verified |
| Sunken Valley treasure Prayer Bead 1 | 1700020 | 6792 | 1700025 | 51700025 | 3720 | ON | Verified |

How it was verified:
- SoulSplitter maps the listed secondary rows to the listed event flags.
- `ItemLotParam.csv` confirms the secondary row awarded item IDs and `getItemFlagId` values.
- `S0000.sl2` reads all 11 secondary flags as ON through the documented event flag reader.
- Parser tests assert the exact 11 secondary-attributed location IDs and row/flag/item triples.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv

Confidence: Verified for current-save attribution. Unknown for Offering Box behavior and untested save-state variants.

## Verified missing Prayer Bead item-lot rows

What was discovered:
- Thirteen non-shop Prayer Beads are missing by item-lot evidence in `S0000.sl2`.
- Each primary row awards Prayer Bead item ID `4000` and its primary get-item flag is OFF.
- Each paired secondary row awards a non-Prayer-Bead item and its secondary get-item flag is also OFF.

| Primary location | Primary row | Primary flag | Secondary row | Secondary flag | Secondary awarded item ID | State in S0000 | Confidence |
|---|---:|---:|---:|---:|---:|---|---|
| Shinobi Hunter Enshin of Misen Prayer Bead | 10500000 | 6763 | 10500005 | 51000925 | 3704 | both OFF | Verified |
| Seven Ashina Spears - Shikibu Toshikatsu Yamauchi Prayer Bead | 10212000 | 6769 | 10212005 | 51112900 | 3704 | both OFF | Verified |
| Long-arm Centipede Sen'un Prayer Bead | 10400000 | 6772 | 10400005 | 52000945 | 3704 | both OFF | Verified |
| Mibu Village underwater chest Prayer Bead | 1500320 | 6796 | 1500325 | 51500325 | 3720 | both OFF | Verified |
| Fountainhead Palace lake chest Prayer Bead | 2500020 | 6797 | 2500025 | 52500025 | 3720 | both OFF | Verified |
| Sunken Valley treasure Prayer Bead 2 | 1700030 | 6793 | 1700035 | 51700035 | 3720 | both OFF | Verified |
| Sunken Valley treasure Prayer Bead 3 | 1700040 | 6794 | 1700045 | 51700045 | 3720 | both OFF | Verified |
| Hirata Audience Chamber hidden wall Prayer Bead | 1000500 | 6789 | 1000505 | 51000505 | 3720 | both OFF | Verified |
| Senpou Temple underwater Prayer Bead | 2000040 | 6791 | 2000045 | 52000045 | 3720 | both OFF | Verified |
| Headless Ape Prayer Bead 2 | 2016 | 6799 | 2018 | 50002018 | 5400 | both OFF | Verified |
| Juzou the Drunkard Hirata Revisit Prayer Bead | 10700100 | 6782 | 10700105 | 51000955 | 3704 | both OFF | Verified |
| Seven Ashina Spears - Shume Masaji Oniwa Prayer Bead | 10212100 | 6786 | 10212105 | 51112910 | 3704 | both OFF | Verified |
| Shigekichi of the Red Guard Prayer Bead | 10701000 | 6787 | 10701005 | 51100965 | 3704 | both OFF | Verified |

How it was verified:
- Public `ItemLotParam.csv` rows show the primary rows award item ID `4000`.
- The same rows show the paired secondary row IDs, non-Prayer-Bead item IDs, and get-item flag IDs.
- All listed primary and secondary event flags read OFF in `S0000.sl2`.
- Automated tests assert the exact missing ID set and row/flag/item triples.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv

Confidence: Verified for current-save missing status

## Boss Memory award rows

What was discovered:
- Boss Memory evidence now uses generic evidence entities backed by ItemLotParam Memory award flags.
- Public EquipParamGoods rows verify goods IDs `5200` through `5213` as boss Memories.
- Public ItemLotParam rows verify the Memory award row, goods ID, and `getItemFlagId` for each boss.
- In `S0000.sl2`, 12 Memory award flags are ON and 2 are OFF.
- Manual fixture-playthrough verification shows that Memory award flags do not reliably represent current boss defeat state in this first-playthrough save, so these rows are comparison evidence only.

| Boss | Goods ID | ItemLot row | Event flag | State in S0000 | Confidence |
|---|---:|---:|---:|---|---|
| Gyoubu Oniwa | 5200 | 2001 | 50002001 | ON | Verified |
| Guardian Ape | 5204 | 2011 | 50002011 | ON | Verified |
| Headless Ape | 5213 | 2017 | 50002017 | ON | Verified |
| Folding Screen Monkeys | 5203 | 2021 | 50002021 | ON | Verified |
| Lady Butterfly | 5201 | 2031 | 50002031 | ON | Verified |
| Demon of Hatred | 5210 | 2041 | 50002041 | ON | Verified |
| Corrupted Monk | 5205 | 2051 | 50002051 | ON | Verified |
| True Monk | 5208 | 2061 | 50002061 | OFF | Verified flag state; status Unknown |
| Divine Dragon | 5209 | 2071 | 50002071 | OFF | Verified flag state; status Unknown |
| Genichiro | 5202 | 2081 | 50002081 | ON | Verified |
| Great Shinobi Owl | 5206 | 2091 | 50002091 | ON | Verified |
| Owl (Father) | 5207 | 2101 | 50002101 | ON | Verified |
| Isshin Ashina | 5212 | 2121 | 50002121 | ON | Verified |
| Sword Saint Isshin | 5211 | 2131 | 50002131 | ON | Verified |

How it was verified:
- `EquipParamGoods.csv` gives the Memory names for goods IDs `5200` through `5213`.
- `ItemLotParam.csv` gives the Memory award rows and `getItemFlagId` values.
- The parser reads each event flag from `S0000.sl2`.
- Automated tests assert all 14 row/flag states, the conservative all-unknown boss status summary, and the regression that Isshin Ashina is not marked defeated from Memory evidence. Headless Ape is uncertain and also remains unknown because Memory evidence is insufficient.

Evidence/source:
- `data/sekiro/bosses.json`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv

Confidence: Verified for Memory award flag state only. Unknown for boss defeated/not-defeated status until true boss defeat/progression flags are mapped.

## ShopLineupParam rows

What was discovered:
- The two Gourd Seed merchant rows are verified from public ShopLineupParam row data:
  - Row `1100101`: Battlefield Memorial Mob, equip ID `4400`, EventFlag `71101210`, sellQuantity `1`.
  - Row `1100400`: Fujioka the Info Broker, equip ID `4400`, EventFlag `71102000`, sellQuantity `1`.
- Equip ID `4400` maps to full goods item ID `0x40001130`, little-endian `30110040`, matching the verified Gourd Seed item ID.
- In `S0000.sl2`, Battlefield Memorial Mob is collected and Fujioka is missing.
- The Abandoned Dungeon Memorial Mob Prayer Bead row is verified from public ShopLineupParam row data:
  - Row `1110000`: equip ID `4000`, EventFlag `71111000`, price `1400`, sellQuantity `1`.
- Equip ID `4000` maps to full goods item ID `0x40000FA0`, little-endian `A00F0040`, matching the verified Prayer Bead item ID.
- In `S0000.sl2`, the Abandoned Dungeon Memorial Mob Prayer Bead shop flag is OFF and its exact-location status is missing by verified shop-purchase evidence.

How it was verified:
- Paramdex confirms the param has event-related fields.
- Public ShopLineupParam row data provides the row values.
- The save does not store these row IDs verbatim; purchase state is read through the row EventFlag values.
- Reading EventFlag `71101210` and `71102000` from `USER_DATA000` reconciles exactly with the save's 7/9 Gourd Seed count.
- Reading EventFlag `71111000` from `USER_DATA000` resolves the Abandoned Dungeon Memorial Mob Prayer Bead shop flag state for this save, but it does not solve the Prayer Bead aggregate count mismatch.

Evidence/source:
- `data/sekiro/gourd-seeds.json`
- `data/sekiro/prayer-beads.json`
- Paramdex ShopLineupParam definition: https://github.com/soulsmods/Paramdex/blob/master/SDT/Defs/ShopLineupParam.xml
- ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv

Confidence: Verified for the two Gourd Seed merchant rows and the Abandoned Dungeon Memorial Mob Prayer Bead row in this save
