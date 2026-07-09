# Prayer Beads Research

Last updated: 2026-07-07

## Inventory-derived count

What was discovered:
- The provided save has 6 Prayer Necklaces and 2 unused Prayer Beads.
- Derived Prayer Beads found: `6 * 4 + 2 = 26 / 40`.
- Derived Prayer Beads missing: 14.
- The currently mapped primary pickup/shop event flags report 15 ON and 25 OFF states.
- The primary event-flag state count alone does not reconcile with the carried inventory-derived Prayer Bead total in this save.
- Eleven OFF-primary locations have verified secondary ItemLotParam reward/replacement flags ON in `S0000.sl2`.
- The remaining 14 locations have verified reward/pickup or shop-purchase evidence flags OFF.
- The parser now reports 15 collected by primary flag, 11 collected by verified secondary ItemLotParam evidence, 14 missing by verified evidence, and 0 unknown.

How it was verified:
- Scanned `USER_DATA000` for necklace item IDs and Prayer Bead item ID `A00F0040`.
- Read every mapped primary Prayer Bead event flag through the documented `0xE8000` event flag reader.
- Read the newly mapped secondary ItemLotParam flags through the same event flag reader.
- Regenerated `exact_location_report.json` and asserted that Prayer Bead locations have 26 collected-by-evidence statuses, 14 missing-by-evidence statuses, 0 unknown statuses, and an 11-bead inventory/primary-flag gap fully attributed by verified secondary ItemLotParam flags.

Evidence/source:
- `data/sekiro/item-ids.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save's aggregate count, the 11 secondary ItemLotParam collected attributions, and the 14 missing-by-evidence statuses. Broader NG+/Offering Box behavior remains Unknown.

## Reconciliation model

What was discovered:
- Primary Prayer Bead mappings cover 40 / 40 known locations, but primary flags alone do not represent the save's aggregate collected count.
- `S0000.sl2` has 26 inventory/progression-derived Prayer Beads and only 15 ON primary pickup/shop flags.
- Eleven collected Prayer Beads are not represented by the current ON primary flag set, but are now represented by verified secondary ItemLotParam reward/replacement flags.
- The remaining 14 Prayer Beads are missing by evidence: their verified primary reward/pickup or shop-purchase flag is OFF, and for non-shop rows the paired secondary replacement/reward flag is also OFF.
- Prayer Necklace count affects the derived total: each necklace contributes 4 consumed Prayer Beads, then unused Prayer Beads are added.
- Current parser evidence fields per Prayer Bead are `primaryPickupFlag`, `bossDefeatFlag`, `itemLotFlag`, `shopFlag`, `offeringBoxFlag`, `inventoryEvidence`, and `confidence`.
- `itemLotFlag.secondary` carries verified secondary reward/replacement signals where available.
- `bossDefeatFlag` and `offeringBoxFlag` remain Unknown for exact-location reconciliation in the current data.

How it was verified:
- `parse_sekiro_save()` reads inventory records from `USER_DATA000`, deriving 6 Prayer Necklaces and 2 unused Prayer Beads.
- The same parser reads all 40 mapped primary flags through the documented `0xE8000` layout.
- Public ItemLotParam row data verifies that the secondary rows award non-Prayer-Bead replacement/reward items and carry their own `getItemFlagId` values.
- Automated tests assert `primaryFlagsOn = 15`, `primaryFlagsOff = 25`, `inventoryDerivedFound = 26`, `unrepresentedCollectedCount = 11`, `attributedBySecondaryItemLotFlags = 11`, `remainingUnattributedCount = 0`, `collectedByEvidence = 26`, `missingByEvidence = 14`, and `unknownByEvidence = 0`.
- Tests also assert that an OFF primary flag is reported as missing only when its verified missing-evidence rule is satisfied.

Evidence/source:
- `research/reference/analyzer.py`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- PowerPyx Prayer Bead guide notes that Prayer Beads can be obtained as drops, purchases, pickups, and Offering Box replacements, and that already found beads transfer to later playthroughs.
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- sekiro-online ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv

Confidence: Verified for the mismatch, aggregate inventory derivation, secondary ItemLotParam collected attribution, missing-by-evidence classification in `S0000.sl2`, and parser/report behavior. Unknown for boss defeat flags, Offering Box flags, and broader NG+/carryover semantics.

## Secondary ItemLot reconciliation in S0000

What was discovered:
- The 11-bead gap between inventory/progression total (26) and ON primary Prayer Bead flags (15) is fully explained by verified secondary ItemLotParam reward/replacement flags in `S0000.sl2`.
- Each row below has its primary Prayer Bead flag OFF and a secondary item-lot flag ON.
- These are treated as collected by evidence for this save. Other OFF primary flags were promoted to missing only after paired verified missing evidence was found.

| ID | Primary flag | Secondary row | Secondary flag | Awarded item ID | State | Confidence |
|---|---:|---:|---:|---:|---|---|
| `general_naomori_kawarada_bead` | 6760 | 10200005 | 51100905 | 3704 | ON | Verified |
| `general_kuranosuke_matsumoto` | 6766 | 10202005 | 51110970 | 3704 | ON | Verified |
| `snake_eyes_shirafuji` | 6773 | 11900005 | 51701015 | 3704 | ON | Verified |
| `tokujiro_the_glutton` | 6776 | 10702005 | 51500935 | 3704 | ON | Verified |
| `orin_of_the_water` | 6777 | 70000005 | 51500925 | 3704 | ON | Verified |
| `okami_leader_shizu` | 6784 | 13100005 | 52500905 | 3704 | ON | Verified |
| `ashina_elite_ujinari_mizou` | 6785 | 14001005 | 51110978 | 3704 | ON | Verified |
| `blazing_bull` | 6765 | 13700005 | 51110976 | 3704 | ON | Verified |
| `headless_ape_bead_1` | 6798 | 2017 | 50002017 | 5213 | ON | Verified |
| `mibu_watermill_attic` | 6795 | 1500045 | 51500045 | 3720 | ON | Verified |
| `sunken_valley_treasure_1` | 6792 | 1700025 | 51700025 | 3720 | ON | Verified |

How it was verified:
- SoulSplitter maps each secondary row to its event flag in the same source group as the primary Prayer Bead row.
- Public `ItemLotParam.csv` data confirms the secondary rows award non-Prayer-Bead item IDs and use the listed `getItemFlagId` values.
- `S0000.sl2` shows all 11 listed secondary flags ON through the documented `0xE8000` reader.
- Automated tests assert the exact secondary-attributed ID set and the reconciled `26 / 40` collected-by-evidence count.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- sekiro-online ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv

Confidence: Verified for attribution in the current `S0000.sl2` save. Unknown for whether the same secondary semantics cover every possible NG+ or Offering Box state without additional saves.

## Missing-by-evidence reconciliation in S0000

What was discovered:
- The 14 remaining Prayer Beads are missing by verified evidence in the current `S0000.sl2` save.
- For 13 non-shop locations, the primary ItemLotParam row awards Prayer Bead item ID `4000`, the primary flag is OFF, and the paired secondary/replacement row flag is also OFF.
- For the Abandoned Dungeon Memorial Mob bead, ShopLineupParam row `1110000` sells Prayer Bead equip ID `4000` and purchase flag `71111000` is OFF.
- Current save evidence status is now `26 collected / 14 missing / 0 unknown`.

| ID | Primary row/flag | Secondary row/flag | State | Confidence |
|---|---|---|---|---|
| `shinobi_hunter_enshin` | 10500000 / 6763 | 10500005 / 51000925 | both OFF | Verified |
| `seven_ashina_spears_shikibu` | 10212000 / 6769 | 10212005 / 51112900 | both OFF | Verified |
| `long_arm_centipede_senun` | 10400000 / 6772 | 10400005 / 52000945 | both OFF | Verified |
| `mibu_underwater_chest` | 1500320 / 6796 | 1500325 / 51500325 | both OFF | Verified |
| `fountainhead_underwater_chest` | 2500020 / 6797 | 2500025 / 52500025 | both OFF | Verified |
| `sunken_valley_treasure_2` | 1700030 / 6793 | 1700035 / 51700035 | both OFF | Verified |
| `sunken_valley_treasure_3` | 1700040 / 6794 | 1700045 / 51700045 | both OFF | Verified |
| `hirata_audience_chamber_hidden_chest` | 1000500 / 6789 | 1000505 / 51000505 | both OFF | Verified |
| `senpou_temple_underwater` | 2000040 / 6791 | 2000045 / 52000045 | both OFF | Verified |
| `headless_ape_bead_2` | 2016 / 6799 | 2018 / 50002018 | both OFF | Verified |
| `juzou_the_drunkard_hirata_revisit` | 10700100 / 6782 | 10700105 / 51000955 | both OFF | Verified |
| `seven_ashina_spears_shume` | 10212100 / 6786 | 10212105 / 51112910 | both OFF | Verified |
| `shigekichi_red_guard` | 10701000 / 6787 | 10701005 / 51100965 | both OFF | Verified |
| `abandoned_dungeon_memorial_mob` | shop row 1110000 / 71111000 | n/a | purchase flag OFF | Verified |

How it was verified:
- Public `ItemLotParam.csv` confirms every listed primary non-shop row awards Prayer Bead item ID `4000`.
- The same row data confirms each paired secondary row awards a non-Prayer-Bead item and stores the listed `getItemFlagId`.
- Public `ShopLineupParam.csv` confirms row `1110000` sells equip ID `4000` with EventFlag `71111000`.
- `S0000.sl2` reads all listed primary flags and secondary/shop missing-evidence flags as OFF through the documented `0xE8000` event flag reader.
- Automated tests assert the exact 14 missing IDs, each missing-evidence rule, and every secondary/shop OFF state.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- sekiro-online ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- sekiro-online ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv

Confidence: Verified for current-save missing status. Exact world-location ordering for the generic Sunken Valley treasure rows remains Unknown and is still tracked separately.

## Sampled exact Prayer Bead primary flags

Note: Rows below describe primary flag state in `S0000.sl2`. Historical `missing` labels in older batch notes mean the primary flag was OFF; after reconciliation hardening, OFF primary flags required secondary evidence before being represented as exact-location missing status.

What was discovered:

| Entry | Event flag | State in S0000 | Confidence |
|---|---:|---|---|
| General Naomori Kawarada Prayer Bead | 6760 | missing | Verified |
| Chained Ogre Prayer Bead | 6761 | collected | Verified |
| General Tenzen Yamauchi Prayer Bead | 6762 | collected | Verified |
| Shinobi Hunter Enshin of Misen Prayer Bead | 6763 | missing | Verified |
| Juzou the Drunkard Prayer Bead | 6764 | collected | Verified |
| Blazing Bull Prayer Bead | 6765 | missing | Verified |
| General Kuranosuke Matsumoto Prayer Bead | 6766 | missing | Verified |
| Ashina Elite - Jinsuke Saze Prayer Bead | 6767 | collected | Verified |
| Seven Ashina Spears - Shikibu Toshikatsu Yamauchi Prayer Bead | 6769 | missing | Verified |
| Lone Shadow Longswordsman Prayer Bead | 6770 | collected | Verified |
| Armored Warrior Prayer Bead | 6771 | collected | Verified |
| Long-arm Centipede Sen'un Prayer Bead | 6772 | missing | Verified |
| Snake Eyes Shirafuji Prayer Bead | 6773 | missing | Verified |
| Long-arm Centipede Giraffe Prayer Bead | 6774 | collected | Verified |
| Snake Eyes Shirahagi Prayer Bead | 6775 | collected | Verified |
| Tokujiro the Glutton Prayer Bead | 6776 | missing | Verified |
| O'Rin of the Water Prayer Bead | 6777 | missing | Verified |
| Chained Ogre Ashina Castle Prayer Bead | 6778 | collected | Verified |
| Lone Shadow Vilehand Prayer Bead | 6779 | collected | Verified |
| Lone Shadow Masanaga the Spear-Bearer Prayer Bead | 6780 | collected | Verified |
| Lone Shadow Masanaga the Spear-Bearer Hirata Revisit Prayer Bead | 6781 | collected | Verified |
| Juzou the Drunkard Hirata Revisit Prayer Bead | 6782 | missing | Verified |
| Sakura Bull of the Palace Prayer Bead | 6783 | collected | Verified |
| Okami Leader Shizu Prayer Bead | 6784 | missing | Verified |
| Ashina Elite - Ujinari Mizou Prayer Bead | 6785 | missing | Verified |
| Seven Ashina Spears - Shume Masaji Oniwa Prayer Bead | 6786 | missing | Verified |
| Shigekichi of the Red Guard Prayer Bead | 6787 | missing | Verified |
| Ashina Castle Gate attic Prayer Bead | 6788 | collected | Verified |
| Hirata Audience Chamber hidden wall Prayer Bead | 6789 | missing | Verified |
| Ashina Castle hidden wall chest Prayer Bead | 6790 | collected | Verified |
| Senpou Temple underwater Prayer Bead | 6791 | missing | Verified |
| Mibu Village underwater chest Prayer Bead | 6796 | missing | Verified |
| Fountainhead Palace lake chest Prayer Bead | 6797 | missing | Verified |
| Sunken Valley treasure Prayer Bead 1 | 6792 | missing | Verified |
| Sunken Valley treasure Prayer Bead 2 | 6793 | missing | Verified |
| Sunken Valley treasure Prayer Bead 3 | 6794 | missing | Verified |
| Watermill attic Prayer Bead | 6795 | missing | Verified |
| Headless Ape Prayer Bead 1 | 6798 | missing | Verified |
| Headless Ape Prayer Bead 2 | 6799 | missing | Verified |
| Abandoned Dungeon Memorial Mob Prayer Bead | 71111000 | missing | Verified |

How it was verified:
- Event flags were sourced from SoulSplitter item pickup rows.
- Exact human-readable locations were cross-checked against the PowerPyx Prayer Bead location guide.
- States were read from `USER_DATA000` with the documented `0xE8000` event flag reader.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- PowerPyx Prayer Bead guide: https://www.powerpyx.com/sekiro-shadows-die-twice-all-prayer-bead-locations/
- `research/reports/exact_location_report.json`

Confidence: Verified for these sampled entries

## Batch 2026-07-07: sixteen additional primary Prayer Beads

What was discovered:
- Sixteen additional primary Prayer Bead locations now have source-backed mappings.
- This brings the structured primary location table to 40 / 40 entries.
- In `S0000.sl2`, one of the sixteen new flags is ON and fifteen are OFF.

| ID | Row ID | Event flag | Save evidence | State | Confidence |
|---|---:|---:|---|---|---|
| `ashina_castle_gate_attic_chest` | 1100310 | 6788 | `USER_DATA000[0xE8350]` bit 4 ON | collected | Verified |
| `blazing_bull` | 13700000 | 6765 | `USER_DATA000[0xE834D]` bit 5 OFF | missing | Verified |
| `hirata_audience_chamber_hidden_chest` | 1000500 | 6789 | `USER_DATA000[0xE8350]` bit 5 OFF | missing | Verified |
| `abandoned_dungeon_memorial_mob` | 1110000 | 71111000 | `USER_DATA000[0xEB633]` bit 0 OFF | missing | Verified |
| `senpou_temple_underwater` | 2000040 | 6791 | `USER_DATA000[0xE8350]` bit 7 OFF | missing | Verified |
| `tokujiro_the_glutton` | 10702000 | 6776 | `USER_DATA000[0xE834F]` bit 0 OFF | missing | Verified |
| `orin_of_the_water` | 70000000 | 6777 | `USER_DATA000[0xE834F]` bit 1 OFF | missing | Verified |
| `mibu_watermill_attic` | 1500040 | 6795 | `USER_DATA000[0xE8351]` bit 3 OFF | missing | Verified |
| `snake_eyes_shirafuji` | 11900000 | 6773 | `USER_DATA000[0xE834E]` bit 5 OFF | missing | Verified |
| `headless_ape_bead_1` | 2015 | 6798 | `USER_DATA000[0xE8351]` bit 6 OFF | missing | Verified |
| `headless_ape_bead_2` | 2016 | 6799 | `USER_DATA000[0xE8351]` bit 7 OFF | missing | Verified |
| `juzou_the_drunkard_hirata_revisit` | 10700100 | 6782 | `USER_DATA000[0xE834F]` bit 6 OFF | missing | Verified |
| `okami_leader_shizu` | 13100000 | 6784 | `USER_DATA000[0xE8350]` bit 0 OFF | missing | Verified |
| `seven_ashina_spears_shume` | 10212100 | 6786 | `USER_DATA000[0xE8350]` bit 2 OFF | missing | Verified |
| `ashina_elite_ujinari_mizou` | 14001000 | 6785 | `USER_DATA000[0xE8350]` bit 1 OFF | missing | Verified |
| `shigekichi_red_guard` | 10701000 | 6787 | `USER_DATA000[0xE8350]` bit 3 OFF | missing | Verified |

How it was verified:
- SoulSplitter item pickup flags provide ItemLotParam row to event flag mappings for the non-shop rows.
- Public ShopLineupParam row data maps Abandoned Dungeon Memorial Mob row `1110000` to equip ID `4000`, price `1400`, sell quantity `1`, and event flag `71111000`; equip ID `4000` matches the verified Prayer Bead goods item ID `A00F0040`.
- PowerPyx provides exact human-readable location/source names.
- The current `S0000.sl2` save was read through the documented `0xE8000` event flag layout.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv
- PowerPyx Prayer Bead guide: https://www.powerpyx.com/sekiro-shadows-die-twice-all-prayer-bead-locations/
- `S0000.sl2`

Confidence: Verified for primary row/event/save-state mapping and guide-backed location names in this batch

## Batch 2026-07-07: eleven additional Prayer Beads

What was discovered:
- Eleven additional Prayer Bead ItemLotParam rows have verified event flags and exact guide-backed location names.
- All eleven are collected in the current `S0000.sl2`.
- Total structured Prayer Bead coverage is now 24 / 40 entries.

| ID | Row ID | Event flag | Save evidence | State | Confidence |
|---|---:|---:|---|---|---|
| `chained_ogre_outskirts` | 50201000 | 6761 | `USER_DATA000[0xE834D]` bit 1 ON | collected | Verified |
| `juzou_the_drunkard_hirata` | 10700000 | 6764 | `USER_DATA000[0xE834D]` bit 4 ON | collected | Verified |
| `ashina_elite_jinsuke_saze` | 14000000 | 6767 | `USER_DATA000[0xE834D]` bit 7 ON | collected | Verified |
| `lone_shadow_longswordsman` | 14702000 | 6770 | `USER_DATA000[0xE834E]` bit 2 ON | collected | Verified |
| `armored_warrior` | 11300000 | 6771 | `USER_DATA000[0xE834E]` bit 3 ON | collected | Verified |
| `snake_eyes_shirahagi` | 11901100 | 6775 | `USER_DATA000[0xE834E]` bit 7 ON | collected | Verified |
| `chained_ogre_ashina_castle` | 50200000 | 6778 | `USER_DATA000[0xE834F]` bit 2 ON | collected | Verified |
| `lone_shadow_vilehand` | 14700000 | 6779 | `USER_DATA000[0xE834F]` bit 3 ON | collected | Verified |
| `lone_shadow_masanaga_serpent_shrine` | 14701000 | 6780 | `USER_DATA000[0xE834F]` bit 4 ON | collected | Verified |
| `lone_shadow_masanaga_hirata_revisit` | 14703100 | 6781 | `USER_DATA000[0xE834F]` bit 5 ON | collected | Verified |
| `sakura_bull` | 13800000 | 6783 | `USER_DATA000[0xE834F]` bit 7 ON | collected | Verified |

How it was verified:
- SoulSplitter item pickup flags provide ItemLotParam row to event flag mappings.
- PowerPyx provides exact human-readable location and source enemy names for each Prayer Bead.
- The current `S0000.sl2` save was read through the documented `0xE8000` event flag layout.
- Only ON-state candidates with strong row/location/source agreement were added in this batch. OFF-state candidates that would require more cross-checking were left Unknown instead of being inferred.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- PowerPyx Prayer Bead guide: https://www.powerpyx.com/sekiro-shadows-die-twice-all-prayer-bead-locations/
- `S0000.sl2`

Confidence: Verified for row/event/save-state mapping and exact guide-backed location names in this batch

## Deferred Unknown candidates

What was discovered:
- The known primary Prayer Bead location table is now mapped to 40 / 40 entries.
- Offering Box replacement behavior remains Unknown.
- The exact row-to-location ordering for the already-mapped Valley treasure rows `1700020`, `1700030`, and `1700040` remains Unknown.

How it was verified:
- The 16 previously deferred primary candidates were promoted only after source and save-state verification.
- No Offering Box replacement row or EMEVD coordinate evidence has been added yet.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- `S0000.sl2`

Confidence: Unknown

## Batch 2026-07-07: five additional Prayer Beads

What was discovered:

| ID | Row ID | Event flag | Save evidence | State | Confidence |
|---|---:|---:|---|---|---|
| `shinobi_hunter_enshin` | 10500000 | 6763 | `USER_DATA000[0xE834D]` bit 3 OFF | missing | Verified |
| `general_kuranosuke_matsumoto` | 10202000 | 6766 | `USER_DATA000[0xE834D]` bit 6 OFF | missing | Verified |
| `seven_ashina_spears_shikibu` | 10212000 | 6769 | `USER_DATA000[0xE834E]` bit 1 OFF | missing | Verified |
| `long_arm_centipede_senun` | 10400000 | 6772 | `USER_DATA000[0xE834E]` bit 4 OFF | missing | Verified |
| `long_arm_centipede_giraffe` | 10401100 | 6774 | `USER_DATA000[0xE834E]` bit 6 ON | collected | Verified |

How it was verified:
- SoulSplitter item pickup flags provide the ItemLotParam row to event flag mapping.
- PowerPyx provides exact human-readable location and source enemy for each Prayer Bead.
- The current `S0000.sl2` save was read through `research/reference/analyzer.py`.
- The observed states do not complete the 40-location table; they only expand the verified partial batch.

Evidence/source:
- `data/sekiro/prayer-beads.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- PowerPyx Prayer Bead guide: https://www.powerpyx.com/sekiro-shadows-die-twice-all-prayer-bead-locations/
- `S0000.sl2`

Confidence: Verified for row/event/save-state mapping and exact guide-backed location names in this batch

## Complete 40-location table

What was discovered:
- The 40 primary Prayer Bead locations are now mapped.
- The parser must not claim Offering Box replacement availability or reconcile current-cycle event flags to carried inventory totals until those semantics are verified.

How it was verified:
- 40 primary Prayer Bead mappings exist in `data/sekiro/prayer-beads.json`.

Evidence/source:
- `data/sekiro/prayer-beads.json`

Confidence: Verified for primary location/event mapping; Unknown for replacement and current-cycle/carryover reconciliation behavior
