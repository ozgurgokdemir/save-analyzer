# Key Items Research

Last updated: 2026-07-08

## Inventory Evidence

What was discovered:
- Key Items are now analyzed as their own category with statuses `collected`, `missing`, and `unknown`.
- Ownership detection uses only verified goods inventory records in `USER_DATA000`.
- The mapped item IDs come from `EquipParamGoods.csv` rows for progression items, ending items, Esoteric Texts, and raw Prosthetic Tool source items.
- The current save resolves 33 mapped Key Items as 12 collected, 6 missing, and 15 unknown.
- Acquisition metadata is stored separately from ownership evidence. It is user guidance and does not drive item status.
- The report keeps `ownershipEvidence` for readability and also exposes the same records through the normalized entity `evidence` field.
- Quest-context items with unresolved retention/consumption semantics are `unknown` when absent.
- Raw Prosthetic Tool source items are `unknown` when absent because they can be consumed or transformed when fitted by the Sculptor.
- No Key Item acquisition event flags are mapped yet.

| Key item | EquipParamGoods row | Item ID hex | State in S0000 | Status | Confidence |
|---|---:|---|---|---|---|
| Divine Dragon's Tears | 9000 | `28230040` | absent | missing | Verified |
| Frozen Tears | 9091 | `83230040` | absent | missing | Verified |
| Fresh Serpent Viscera | 9192 | `E8230040` | absent | missing | Verified |
| Dried Serpent Viscera | 9193 | `E9230040` | present at `0x96980` | collected | Verified |
| Father's Bell Charm | 9011 | `33230040` | absent | missing | Verified |
| Aromatic Flower | 2503 | `C7090040` | absent | missing | Verified |
| Aromatic Branch | 2502 | `C6090040` | present at `0x96960` | collected | Verified |
| Mortal Blade | 2400 | `60090040` | present at `0x96920` | collected | Verified |
| Shelter Stone | 2501 | `C5090040` | present at `0x96930` | collected | Verified |
| Lotus of the Palace | 2500 | `C4090040` | present at `0x969a0` | collected | Verified |
| Shinobi Esoteric Text | 2920 | `680B0040` | present at `0x967a0` | collected | Verified |
| Prosthetic Esoteric Text | 2921 | `690B0040` | present at `0x967c0` | collected | Verified |
| Ashina Esoteric Text | 2922 | `6A0B0040` | present at `0x96880` | collected | Verified |
| Senpou Esoteric Text | 2923 | `6B0B0040` | present at `0x96900` | collected | Verified |
| Mushin Esoteric Text | 2924 | `6C0B0040` | absent | missing | Verified |
| Holy Chapter: Dragon's Return | 9209 | `F9230040` | absent | unknown | Unknown |
| Immortal Severance Text | 9210 | `FA230040` | present at `0x96870` | collected | Verified |
| Immortal Severance Scrap | 9211 | `FB230040` | present at `0x969b0` | collected | Verified |
| Fragrant Flower Note | 9212 | `FC230040` | present at `0x96830` | collected | Verified |
| Holy Chapter: Infested | 9215 | `FF230040` | absent | unknown | Unknown |
| Holy Chapter: Infested alternate row | 9228 | `0C240040` | absent | unknown | Unknown |
| Mechanical Barrel | 2910 | `5E0B0040` | absent | unknown | Unknown |
| Shuriken Wheel | 9700 | `E4250040` | absent | unknown | Unknown |
| Robert's Firecrackers | 9710 | `EE250040` | absent | unknown | Unknown |
| Flame Barrel | 9720 | `F8250040` | absent | unknown | Unknown |
| Shinobi Axe of the Monkey | 9730 | `02260040` | absent | unknown | Unknown |
| Mist Raven's Feathers | 9740 | `0C260040` | absent | unknown | Unknown |
| Sabimaru | 9750 | `16260040` | absent | unknown | Unknown |
| Iron Fortress | 9760 | `20260040` | absent | unknown | Unknown |
| Large Fan | 9770 | `2A260040` | absent | unknown | Unknown |
| Gyoubu's Broken Horn | 9780 | `34260040` | absent | unknown | Unknown |
| Slender Finger | 9790 | `3E260040` | absent | unknown | Unknown |
| Malcontent's Ring | 9791 | `3F260040` | absent | unknown | Unknown |

How it was verified:
- Read `EquipParamGoods.csv` row IDs and names from the public `sekiro-online/params` dump.
- Scanned `USER_DATA000` in `S0000.sl2` for each little-endian goods row ID plus `0x40` item category byte.
- Required present records to match the same goods inventory shape already used by the parser, including the observed mirror-prefix pattern and quantity `1` for the current save records.
- Added automated tests requiring every mapped Key Item to resolve to the exact current save status above.
- Added tests requiring absent Prosthetic Tool source items and quest-context texts to remain `unknown` where retention semantics are unresolved.
- Added schema consistency tests requiring Key Items to expose shared entity fields and status-keyed summary counts.

Evidence/source:
- `data/sekiro/key-items.json`
- `research/reference/analyzer.py`
- `research/reports/exact_location_report.json`
- `research/reference/tests/test_analyzer.py`
- sekiro-online `EquipParamGoods.csv`: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- Fextralife Endings page, used only for acquisition and route guidance: https://sekiroshadowsdietwice.wiki.fextralife.com/Endings
- Fextralife Esoteric Text and Prosthetic source item pages, used only for acquisition guidance.
- `S0000.sl2` SHA-256 `90f24808ee063c7b320298c739ac4bd0ce430831970f63a009d39ee2e3b615fc`

Confidence: Verified for mapped EquipParamGoods row IDs, current save inventory presence, and current save inventory absence. Probable for acquisition metadata from community guide pages. Unknown for quest-context retention semantics, Prosthetic Tool source item consumption state, and acquisition event flags.

## Endings Integration

What was discovered:
- Ending availability evidence now references Key Item analyzer entities with `type = key_item` and `keyItemId`.
- Endings no longer duplicate their own Key Item table or perform separate status-driving inventory scans for route items.
- Persistent missing Key Items can make a route `incomplete`.
- Unknown Key Items stay unknown and do not become missing route requirements unless the ending mapping marks them as required and their retention semantics are verified.
- `Holy Chapter` quest-context items remain advisory evidence for Return and are not used as blockers.
- Ending evidence embeds compact Key Item references so route analysis and Key Item ownership stay synchronized.

How it was verified:
- Updated `data/sekiro/endings.json` to reference `data/sekiro/key-items.json` IDs for all route item evidence.
- Added automated tests requiring ending route evidence to include the compact referenced Key Item entity and its `ownershipEvidence`.
- Confirmed the current ending summary remains: Shura `unknown`, Immortal Severance `incomplete`, Purification `incomplete`, Return `incomplete`.

Evidence/source:
- `data/sekiro/endings.json`
- `data/sekiro/key-items.json`
- `docs/research/endings.md`
- `research/reference/tests/test_analyzer.py`
- `research/reports/exact_location_report.json`

Confidence: Verified for parser integration and current save output. Unknown for ending completion flags and hidden NPC quest-step flags.
