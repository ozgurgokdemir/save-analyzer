# Key Items Research

Last updated: 2026-07-16

## Status evidence

Key Items use two verified evidence paths:

- retained items use goods inventory records in `USER_DATA000`;
- consumed, transformed, or superseded items use persistent ItemLot/Shop acquisition flags.

A mapped item is `collected` when retained inventory is present or any mapped acquisition flag is ON. It is `missing` when retained inventory is absent and every mapped acquisition flag is OFF. It remains `unknown` only when the required evidence cannot be decoded. Community acquisition guidance never drives status.

The reference fixture resolves all 33 mapped Key Items as 22 collected, 11 missing, and 0 unknown.

## Acquisition-backed items

| Key item | Persistent flag evidence | Reference status |
|---|---|---|
| Holy Chapter: Dragon's Return | ItemLot `52000010` | missing |
| Holy Chapter: Infested | ItemLot `50006320` | missing |
| Holy Chapter: Infested alternate row | ItemLot `50006320` | missing |
| Mechanical Barrel | ItemLot `6740` | collected |
| Shuriken Wheel | ItemLot `6500` | collected |
| Robert's Firecrackers | Shop `71101000` or `71102300` | collected |
| Flame Barrel | ItemLot `6502` | collected |
| Shinobi Axe of the Monkey | ItemLot `6503` | collected |
| Mist Raven's Feathers | ItemLot `6504` | collected |
| Sabimaru | ItemLot `6505` | collected |
| Iron Fortress | Shop `71111500` | missing |
| Large Fan | ItemLot `6507` | collected |
| Gyoubu's Broken Horn | ItemLot `6508` | collected |
| Slender Finger | ItemLot `6509` | collected |
| Malcontent's Ring | ItemLot `6743` | missing |

The two Holy Chapter: Infested mappings represent alternate goods rows for the same logical item and intentionally share flag `50006320`. They therefore cannot be distinguished as separate pickups in a save.

## Verification

- `EquipParamGoods.csv` supplies mapped goods row identities.
- `ItemLotParam.csv` and `ShopLineupParam.csv` supply persistent acquisition flags.
- The verified event-flag decoder reads those flags from all three sanitized fixtures.
- Regression tests assert zero unknown Key Items, exact summary counts, and the acquisition-backed missing set.
- The privacy test covers every committed fixture.

Evidence/source:

- `data/sekiro/key-items.json`
- `packages/analyzer/src/sekiro/index.ts`
- `packages/analyzer/test/sekiro-golden.test.ts`
- `research/fixtures/README.md`
- EquipParamGoods: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- ItemLotParam: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- ShopLineupParam: https://github.com/sekiro-online/params/blob/master/src/ShopLineupParam.csv

Confidence: Verified for mapped inventory and persistent acquisition evidence. Acquisition descriptions sourced only from community guides remain guidance-level metadata.

## Endings integration

Ending availability references Key Item analyzer entities rather than duplicating inventory scans. Persistent missing route items can make an ending `incomplete`; `blocked` still requires verified permanent lockout evidence. Holy Chapter items are reported accurately in the Key Items category but remain advisory for Return route logic until the relevant quest-step and ending flags are mapped.

The reference ending summary remains Shura `unknown`, with Immortal Severance, Purification, and Return `incomplete`.