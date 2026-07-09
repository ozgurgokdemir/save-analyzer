# Gourd Seeds Research

Last updated: 2026-07-07

## Inventory-derived count

What was discovered:
- Healing Gourd uses: 8
- Unused Gourd Seeds: 0
- Derived Gourd Seeds found: `8 - 1 + 0 = 7 / 9`
- Derived Gourd Seeds missing: 2

How it was verified:
- Scanned `USER_DATA000` for Healing Gourd and Gourd Seed item IDs.

Evidence/source:
- `data/sekiro/item-ids.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save

## Exact non-shop Gourd Seed flags

What was discovered:

| Entry | Row ID | Event flag | State in S0000 | Confidence |
|---|---:|---:|---|---|
| General Naomori Kawarada | 10200001 | 6723 | collected | Verified |
| Building after Chained Ogre | 1100200 | 6725 | collected | Verified |
| Upper Tower Antechamber chest | 1110020 | 6726 | collected | Verified |
| Senpou Temple treasure | 2000730 | 6727 | collected | Verified |
| Sunken Valley treasure | 1700820 | 6724 | missing | Verified |
| Mibu Village glowing tree | 1500010 | 6728 | collected | Verified |
| Palace Grounds chest | 2500000 | 6729 | collected | Verified |

How it was verified:
- Row/event mappings come from SoulSplitter's Sekiro item pickup flags.
- States were read from `USER_DATA000` with the low event flag reader.
- The non-shop exact states reconcile with the inventory-derived total.

Evidence/source:
- `data/sekiro/gourd-seeds.json`
- SoulSplitter item pickup flags: https://github.com/FrankvdStam/SoulSplitter/wiki/Sekiro-item-pickup-flags
- `research/reports/exact_location_report.json`

Confidence: Verified

## Confirmed missing in S0000

What was discovered:
- Sunken Valley treasure Gourd Seed is missing.
- Event flag 6724 is OFF.
- Fujioka the Info Broker shop Gourd Seed is missing.
- ShopLineupParam row 1100400 event flag 71102000 is OFF.

How it was verified:
- `data/sekiro/gourd-seeds.json` maps row `1700820` to event flag `6724`.
- `data/sekiro/gourd-seeds.json` maps shop row `1100400` to event flag `71102000`.
- `research/reference/analyzer.py` reads flag 6724 and flag 71102000 as false in `USER_DATA000`.

Evidence/source:
- `S0000.sl2`
- `research/reports/exact_location_report.json`

Confidence: Verified

## Merchant Gourd Seed state

What was discovered:
- Battlefield Memorial Mob purchase is collected.
- Fujioka the Info Broker purchase is missing.
- The previously unresolved shop seed is Fujioka.

| Entry | ShopLineupParam row | Equip ID | Event flag | State in S0000 | Save evidence | Confidence |
|---|---:|---:|---:|---|---|---|
| Battlefield Memorial Mob purchase | 1100101 | 4400 | 71101210 | collected | `USER_DATA000[0xEB16B]` bit 2 ON | Verified |
| Fujioka the Info Broker purchase | 1100400 | 4400 | 71102000 | missing | `USER_DATA000[0xEB1CE]` bit 0 OFF | Verified |

How it was verified:
- Public ShopLineupParam row data maps row `1100101` to EventFlag `71101210`, price `1000`, sellQuantity `1`.
- Public ShopLineupParam row data maps row `1100400` to EventFlag `71102000`, price `2000`, sellQuantity `1`.
- Both rows sell equip ID `4400`. The verified Gourd Seed save item ID is little-endian `30110040`, which is full goods ID `0x40001130`; lower goods ID `0x1130` is decimal `4400`.
- Event flags are read from `USER_DATA000` with bit index `eventFlag % 1000000` at base `0xE8000`, LSB-first.
- The resolved states reconcile exactly with the save count: six non-shop seeds collected + Battlefield shop seed collected = 7/9; Sunken Valley + Fujioka are the two missing seeds.

Evidence/source:
- `data/sekiro/gourd-seeds.json`
- `data/sekiro/event-flag-layout.json`
- `research/reports/exact_location_report.json`
- ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv
- Paramdex ShopLineupParam definition: https://github.com/soulsmods/Paramdex/blob/master/SDT/Defs/ShopLineupParam.xml

Confidence: Verified for this save

## Shop purchase state

What was discovered:
- Shop purchase state for the two Gourd Seed merchant rows is stored through the `ShopLineupParam` EventFlag field.
- For this save:
  - Event flag `71101210` is ON, so Battlefield Memorial Mob's Gourd Seed is collected.
  - Event flag `71102000` is OFF, so Fujioka's Gourd Seed is missing.

How it was verified:
- Paramdex identifies `eventFlag` as the shop row field that stores quantity state.
- Public ShopLineupParam row data provides the two Gourd Seed merchant row values.
- Save analysis reads those two flags from `S0000.sl2` and reconciles them with the inventory-derived 7/9 total.

Evidence/source:
- Paramdex ShopLineupParam definition: https://github.com/soulsmods/Paramdex/blob/master/SDT/Defs/ShopLineupParam.xml
- ShopLineupParam row data: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv
- `data/sekiro/event-flag-layout.json`
- `data/sekiro/gourd-seeds.json`

Confidence: Verified for this save
