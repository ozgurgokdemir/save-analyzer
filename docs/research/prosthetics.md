# Prosthetics Research

Last updated: 2026-07-08

## Base Prosthetic Tools

What was discovered:
- The ten base Prosthetic Tools are represented by `EquipParamWeapon` rows `70000` through `79000`.
- The raw source items are represented by `EquipParamGoods` rows `9700` through `9790`.
- Source items can be consumed when fitted, so source item inventory presence is not used as ownership evidence.
- In `S0000.sl2`, base weapon inventory records with quantity `1` are present for 9 / 10 base tools.
- `Loaded Umbrella` row `76000` has no matching weapon inventory record with quantity `1` in `USER_DATA000`, so it is reported missing.
- Location/source metadata has been added for all ten base tools from source item guide pages.
- In the current save, the missing tool is `loaded_umbrella`: go to Blackhat Badger in Ashina Castle's Old Grave area, purchase Iron Fortress, then fit it with the Sculptor as Loaded Umbrella.

| Prosthetic Tool | EquipParamWeapon row | Source goods row | Source item | Weapon ID hex | State in S0000 | Status |
|---|---:|---:|---|---|---|---|
| Loaded Shuriken | 70000 | 9700 | Shuriken Wheel | `70110100` | present | collected |
| Shinobi Firecracker | 71000 | 9710 | Robert's Firecrackers | `58150100` | present | collected |
| Flame Vent | 72000 | 9720 | Flame Barrel | `40190100` | present | collected |
| Loaded Axe | 73000 | 9730 | Shinobi Axe of the Monkey | `281D0100` | present | collected |
| Mist Raven | 74000 | 9740 | Mist Raven's Feathers | `10210100` | present | collected |
| Sabimaru | 75000 | 9750 | Sabimaru | `F8240100` | present | collected |
| Loaded Umbrella | 76000 | 9760 | Iron Fortress | `E0280100` | absent | missing |
| Divine Abduction | 77000 | 9770 | Large Fan | `C82C0100` | present | collected |
| Loaded Spear | 78000 | 9780 | Gyoubu's Broken Horn | `B0300100` | present | collected |
| Finger Whistle | 79000 | 9790 | Slender Finger | `98340100` | present | collected |

## Base Tool Location Metadata

What was discovered:
- Each base Prosthetic Tool now has structured `sourceLocation` metadata in `data/sekiro/prosthetics.json`.
- The parser carries this metadata into `parseSekiroSave(...).prosthetics.entities[]`, so a missing tool can report where to go without hardcoded UI logic.
- The location metadata is community-guide backed and marked `Probable`; current-save ownership status remains `Verified` when supported by weapon inventory records.

| Tool | Area | Location/source | Acquisition | Vendor/chest/enemy | Location confidence |
|---|---|---|---|---|---|
| Loaded Shuriken | Ashina Outskirts | Outskirts Wall - Gate Path corpse in nearby building | Loot Shuriken Wheel, then fit as Loaded Shuriken | corpse | Probable |
| Shinobi Firecracker | Ashina Outskirts | Crow's Bed Memorial Mob, cliffs between Outskirts Wall idols | Purchase Robert's Firecrackers, then fit as Shinobi Firecracker | Crow's Bed Memorial Mob | Probable |
| Flame Vent | Hirata Estate | Estate Path campfire surrounded by enemies | Loot Flame Barrel, then fit as Flame Vent | pickup/fire | Probable |
| Loaded Axe | Hirata Estate | Estate Path courtyard small garden house | Loot Shinobi Axe of the Monkey, then fit as Loaded Axe | small garden house / shrine | Probable |
| Mist Raven | Hirata Estate | Bamboo Thicket Slope hidden temple / pagoda path | Loot Mist Raven's Feathers, then fit as Mist Raven | hidden temple guarded by Lone Shadow / purple ninja | Probable |
| Sabimaru | Ashina Castle | Upper Tower - Antechamber lower room | Loot Sabimaru from chest, then fit as Sabimaru | chest | Probable |
| Loaded Umbrella | Ashina Castle | Old Grave area, building below the Old Grave Idol | Purchase Iron Fortress from Blackhat Badger, then fit as Loaded Umbrella | Blackhat Badger | Probable |
| Divine Abduction | Sunken Valley | Gun Fort, Long-arm Centipede Giraffe room Buddha statue | Defeat Long-arm Centipede Giraffe, loot Large Fan, then fit as Divine Abduction | Long-arm Centipede Giraffe / Buddha statue pickup | Probable |
| Loaded Spear | Ashina Reservoir | Locked gatehouse near Moon-View Tower | Use Gatehouse Key and loot Gyoubu's Broken Horn from chest, then fit as Loaded Spear | Gatehouse chest | Probable |
| Finger Whistle | Sunken Valley | Guardian Ape boss reward | Defeat Guardian Ape for Slender Finger, then fit as Finger Whistle | Guardian Ape | Probable |

How it was verified:
- Read the Fextralife source item pages for the ten raw materials and recorded area, acquisition source, and progression notes.
- Cross-checked each location entry against the existing `EquipParamGoods` source item name and `EquipParamWeapon` base tool row already used by the save analyzer.
- Added automated tests that assert every parsed prosthetic entity includes `sourceLocation`, source references, and expected area/source/acquisition metadata.
- Added a regression test for `loaded_umbrella` requiring `status = missing`, source item `Iron Fortress`, vendor `Blackhat Badger`, and the Old Grave acquisition route.

Evidence/source:
- Shuriken Wheel: https://sekiroshadowsdietwice.wiki.fextralife.com/Shuriken+Wheel
- Robert's Firecrackers: https://sekiroshadowsdietwice.wiki.fextralife.com/Robert%27s+Firecrackers
- Flame Barrel: https://sekiroshadowsdietwice.wiki.fextralife.com/Flame+Barrel
- Shinobi Axe of the Monkey: https://sekiroshadowsdietwice.wiki.fextralife.com/Shinobi+Axe+of+the+Monkey
- Mist Raven's Feathers: https://sekiroshadowsdietwice.wiki.fextralife.com/Mist+Raven%27s+Feathers
- Sabimaru: https://sekiroshadowsdietwice.wiki.fextralife.com/Sabimaru
- Iron Fortress: https://sekiroshadowsdietwice.wiki.fextralife.com/Iron+Fortress
- Large Fan: https://sekiroshadowsdietwice.wiki.fextralife.com/Large+Fan
- Gyoubu's Broken Horn: https://sekiroshadowsdietwice.wiki.fextralife.com/Gyoubu%27s+Broken+Horn
- Slender Finger: https://sekiroshadowsdietwice.wiki.fextralife.com/Slender+Finger

Confidence: Probable for exact location/source route metadata from community guide pages; Verified for base tool item IDs, weapon IDs, and current save ownership states.

## Prosthetic Tool Upgrades

What was discovered:
- `EquipParamWeapon.csv` contains 30 Prosthetic Tool upgrade rows in the `70100` through `79200` ranges.
- Upgrade ownership is represented by the same weapon inventory record pattern used by base tools: little-endian weapon row ID, quantity `1`, and the observed `80 80` inventory-record prefix.
- In `S0000.sl2`, 12 / 30 upgrades have verified weapon inventory records and 18 / 30 have verified absence of their own upgrade records.
- Upgrade ownership is not inferred from base tool ownership.
- Missing upgrade status is not inferred from missing prerequisites; it is set only when that upgrade's own verified weapon record is absent.
- Material and tree prerequisite data remains `Unknown` because the inspected public param rows did not provide a verified row-to-material/tree mapping for these upgrades.

| Upgrade | Base tool | EquipParamWeapon row | Weapon ID hex | State in S0000 | Status |
|---|---|---:|---|---|---|
| Spinning Shuriken | Loaded Shuriken | 70100 | `D4110100` | present | unlocked |
| Gouging Top | Loaded Shuriken | 70200 | `38120100` | present | unlocked |
| Phantom Kunai | Loaded Shuriken | 70300 | `9C120100` | absent | missing |
| Sen Throw | Loaded Shuriken | 70400 | `00130100` | absent | missing |
| Lazulite Shuriken | Loaded Shuriken | 70500 | `64130100` | absent | missing |
| Spring-load Firecracker | Shinobi Firecracker | 71100 | `BC150100` | present | unlocked |
| Long Spark | Shinobi Firecracker | 71200 | `20160100` | present | unlocked |
| Purple Fume Spark | Shinobi Firecracker | 71300 | `84160100` | absent | missing |
| Spring-load Flame Vent | Flame Vent | 72100 | `A4190100` | present | unlocked |
| Okinaga's Flame Vent | Flame Vent | 72200 | `081A0100` | absent | missing |
| Lazulite Sacred Flame | Flame Vent | 72300 | `6C1A0100` | absent | missing |
| Spring-load Axe | Loaded Axe | 73100 | `8C1D0100` | present | unlocked |
| Sparking Axe | Loaded Axe | 73200 | `F01D0100` | absent | missing |
| Lazulite Axe | Loaded Axe | 73300 | `541E0100` | absent | missing |
| Aged Feather Mist Raven | Mist Raven | 74100 | `74210100` | present | unlocked |
| Great Feather Mist Raven | Mist Raven | 74200 | `D8210100` | absent | missing |
| Improved Sabimaru | Sabimaru | 75100 | `5C250100` | present | unlocked |
| Piercing Sabimaru | Sabimaru | 75200 | `C0250100` | absent | missing |
| Lazulite Sabimaru | Sabimaru | 75300 | `24260100` | absent | missing |
| Loaded Umbrella - Magnet | Loaded Umbrella | 76100 | `44290100` | absent | missing |
| Suzaku's Lotus Umbrella | Loaded Umbrella | 76200 | `A8290100` | absent | missing |
| Phoenix's Lilac Umbrella | Loaded Umbrella | 76300 | `0C2A0100` | absent | missing |
| Double Divine Abduction | Divine Abduction | 77100 | `2C2D0100` | present | unlocked |
| Golden Vortex | Divine Abduction | 77200 | `902D0100` | absent | missing |
| Loaded Spear Thrust type | Loaded Spear | 78100 | `14310100` | present | unlocked |
| Loaded Spear Cleave type | Loaded Spear | 78200 | `78310100` | present | unlocked |
| Spiral Spear | Loaded Spear | 78300 | `DC310100` | absent | missing |
| Leaping Flame | Loaded Spear | 78400 | `40320100` | absent | missing |
| Mountain Echo | Finger Whistle | 79100 | `FC340100` | present | unlocked |
| Malcontent | Finger Whistle | 79200 | `60350100` | absent | missing |

How it was verified:
- Queried public `EquipParamWeapon.csv` for rows `70000` through `79999` and identified the 30 non-base Prosthetic Tool upgrade rows.
- Scanned `USER_DATA000` for each upgrade row's little-endian weapon ID using the verified weapon inventory record predicate.
- Added `data/sekiro/prosthetic-upgrades.json` as a separate mapping file so upgrades are not mixed with base tools.
- Added parser output under `prostheticUpgrades` with `unlocked`, `missing`, and `unknown` summary counts.
- Added automated tests for all 30 upgrade row IDs, item hex values, status results, and record offsets for the 12 unlocked upgrades.
- Inspected related public param files, including `EquipMtrlSetParam.csv`, `ReinforceParamWeapon.csv`, and `EquipParamWeapon.csv`; no verified upgrade material/tree mapping was promoted.

Evidence/source:
- `data/sekiro/prosthetic-upgrades.json`
- `research/reports/exact_location_report.json`
- `packages/analyzer/test/sekiro-golden.test.ts`
- EquipParamWeapon row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamWeapon.csv
- EquipMtrlSetParam row data: https://github.com/sekiro-online/params/blob/master/src/EquipMtrlSetParam.csv
- ReinforceParamWeapon row data: https://github.com/sekiro-online/params/blob/master/src/ReinforceParamWeapon.csv
- Prosthetic upgrade source context: https://sekiroshadowsdietwice.wiki.fextralife.com/Prosthetic+Tools
- Local save scan performed on `S0000.sl2`

Confidence: Verified for upgrade row IDs, item hex values, current save record states, and unlocked/missing status. Probable for the shared Sculptor upgrade-menu source. Unknown for exact upgrade material costs and tree prerequisites.

How it was verified:
- Read public `EquipParamWeapon.csv` rows `70000`, `71000`, `72000`, `73000`, `74000`, `75000`, `76000`, `77000`, `78000`, and `79000` to verify base Prosthetic Tool names.
- Read public `EquipParamGoods.csv` rows `9700` through `9790` to verify source item names.
- Scanned `USER_DATA000` for little-endian weapon IDs and required an inventory-style record where the two bytes before the ID are `80 80` and the quantity immediately after the ID is `1`.
- Confirmed the matching record offsets for collected tools in `exact_location_report.json`.
- Added automated tests for all ten base tools, including the missing `Loaded Umbrella`.
- Added automated tests for all ten base tool location/source metadata blocks.

Evidence/source:
- `data/sekiro/prosthetics.json`
- `research/reports/exact_location_report.json`
- `packages/analyzer/test/sekiro-golden.test.ts`
- EquipParamWeapon row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamWeapon.csv
- EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- Local save scan performed on `S0000.sl2`

Confidence: Verified for base Prosthetic Tool ownership in this save. Unknown for Prosthetic Tool upgrade tree and raw source item pickup flags.
