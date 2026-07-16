# Endings Research

Last updated: 2026-07-08

## Ending route evidence

What was discovered:
- Ending analysis now uses the generic evidence model for ending-related key items.
- Ending route evidence now references the dedicated Key Items analyzer with `type = key_item` and `keyItemId`, rather than duplicating raw route item inventory scans inside `endings.json`.
- Ending entities preserve `completionEvidence`, `availabilityEvidence`, `missingRequirements`, and `blockEvidence`, while also exposing a combined normalized `evidence` array for API consumers.
- `EquipParamGoods.csv` provides stable row IDs and names for the key items used by Shura, Immortal Severance, Purification, and Return.
- `S0000.sl2` stores these key items as goods inventory records using the same little-endian row ID plus `0x40` category byte pattern used elsewhere in the parser.
- The current save has the non-Shura progression item `Aromatic Branch`, which is probable evidence that the Shura route choice has already been passed on the Kuro branch. Because the permanent-block semantics are not verified from a dedicated route-choice/progression flag, this remains `blockEvidence` and does not force `blocked` status.
- The current save does not have `Divine Dragon's Tears`, so none of the non-Shura final ending choices are currently selectable.
- No verified ending completion event/progression flags are mapped yet.
- Boss Memories and Memory ItemLot flags are not used as ending completion evidence.
- The finalized Endings status model is `completed`, `available`, `incomplete`, `blocked`, and `unknown`.
- Missing route items now produce `incomplete`, not `blocked`, unless verified permanent block evidence exists.

| Key item | EquipParamGoods row | Item ID hex | State in S0000 | Evidence path |
|---|---:|---|---|---|
| Mortal Blade | 2400 | `60090040` | present at `0x96920` | key_item -> inventory_item |
| Lotus of the Palace | 2500 | `C4090040` | present at `0x969a0` | key_item -> inventory_item |
| Shelter Stone | 2501 | `C5090040` | present at `0x96930` | key_item -> inventory_item |
| Aromatic Branch | 2502 | `C6090040` | present at `0x96960` | key_item -> inventory_item |
| Aromatic Flower | 2503 | `C7090040` | absent | key_item -> inventory_item |
| Divine Dragon's Tears | 9000 | `28230040` | absent | key_item -> inventory_item |
| Father's Bell Charm | 9011 | `33230040` | absent | key_item -> inventory_item |
| Frozen Tears | 9091 | `83230040` | absent | key_item -> inventory_item |
| Fresh Serpent Viscera | 9192 | `E8230040` | absent | key_item -> inventory_item |
| Dried Serpent Viscera | 9193 | `E9230040` | present at `0x96980` | key_item -> inventory_item |
| Holy Chapter: Dragon's Return | 9209 | `F9230040` | absent | key_item -> quest-context inventory_item |
| Immortal Severance Text | 9210 | `FA230040` | present at `0x96870` | key_item -> quest-context inventory_item |
| Immortal Severance Scrap | 9211 | `FB230040` | present at `0x969b0` | key_item -> quest-context inventory_item |
| Fragrant Flower Note | 9212 | `FC230040` | present at `0x96830` | key_item -> quest-context inventory_item |
| Holy Chapter: Infested | 9215 | `FF230040` | absent | key_item -> quest-context inventory_item |
| Holy Chapter: Infested | 9228 | `0C240040` | absent | key_item -> quest-context inventory_item |

How it was verified:
- Read public `EquipParamGoods.csv` rows for the ending-related key items.
- Scanned `USER_DATA000` in `S0000.sl2` for each item ID.
- Added `data/sekiro/key-items.json` as the status-driving source for route item ownership and updated endings to reference those Key Item entities.
- Added automated tests requiring the exact present/absent states for all mapped ending-route evidence in this save.
- Added automated tests requiring ending availability evidence to include the referenced Key Item and its nested `ownershipEvidence`.
- Added schema consistency tests requiring ending entities to expose shared entity fields and status-keyed summary counts.
- Added route analysis tests requiring completion evidence to remain Unknown because no completion flag has been verified.
- Added tests requiring the report not to use boss Memory evidence for ending status.

Evidence/source:
- `data/sekiro/endings.json`
- `data/sekiro/key-items.json`
- `research/reports/exact_location_report.json`
- `packages/analyzer/test/sekiro-golden.test.ts`
- sekiro-online EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- Fextralife Endings page, used for community route requirements and final choice guidance: https://sekiroshadowsdietwice.wiki.fextralife.com/Endings
- `S0000.sl2` SHA-256 `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`

Confidence: Verified for EquipParamGoods row names/IDs and current save inventory presence/absence. Probable for route guidance and the Shura potential blocker derived from `Aromatic Branch`. Unknown for ending completion flags, detailed NPC quest-step flags, and verified permanent Shura route lockout evidence.

## Current save ending status

What was discovered:
- `shura` is reported as `unknown`. `Aromatic Branch` is present as probable non-Shura branch `blockEvidence`, but it is not verified permanent block evidence under the finalized status model.
- `immortal_severance` is reported as `incomplete` because `Divine Dragon's Tears` is absent. `Mortal Blade` is present.
- `purification` is reported as `incomplete` because `Divine Dragon's Tears`, `Father's Bell Charm`, and `Aromatic Flower` are absent. `Fragrant Flower Note` is present as quest-context evidence but is not used alone to mark the route available.
- `return` is reported as `incomplete` because `Divine Dragon's Tears`, `Frozen Tears`, and `Fresh Serpent Viscera` are absent. `Dried Serpent Viscera` is present. Holy Chapter items are reported as quest-context only until retention/consumption semantics are verified.
- All four routes have `completionEvidence` set to Unknown because no verified ending completion flag is mapped.

| Ending | Status in S0000 | Required/missing evidence | Confidence |
|---|---|---|---|
| Shura | unknown | `Aromatic Branch` present as probable block evidence, but not verified permanent block evidence | Unknown |
| Immortal Severance | incomplete | missing `Divine Dragon's Tears` | Probable |
| Purification | incomplete | missing `Divine Dragon's Tears`, `Father's Bell Charm`, `Aromatic Flower` | Probable |
| Return | incomplete | missing `Divine Dragon's Tears`, `Frozen Tears`, `Fresh Serpent Viscera`; `Dried Serpent Viscera` present | Probable |

How it was verified:
- The parser analyzed every ending route from `data/sekiro/endings.json`.
- Required key item states come from verified inventory reads in `USER_DATA000`.
- Ending route item states are now resolved through the Key Items analyzer, so acquisition guidance and ownership status stay separate.
- Route instructions come from community ending-route documentation and are marked `Probable`.
- The parser keeps `completionEvidence`, `availabilityEvidence`, `missingRequirements`, and `blockEvidence` separate from the route `status`.

Evidence/source:
- `data/sekiro/endings.json`
- `research/reports/exact_location_report.json`
- Fextralife Endings: https://sekiroshadowsdietwice.wiki.fextralife.com/Endings
- sekiro-online EquipParamGoods: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv

Confidence: Verified for current save key item states. Probable for incomplete route classification from community route requirements. Unknown for Shura status, hidden route-step flags, completed ending flags, and verified permanent block flags.

## Unresolved ending research

What was discovered:
- Ending completion flags are not mapped.
- Purification NPC/eavesdrop step flags are not mapped.
- Return Divine Child quest-step flags are not mapped.
- Holy Chapter retention/consumption semantics are not verified, so Holy Chapter item absence is not used alone as a Return blocker.

How it was verified:
- No source-backed EMEVD or event flag table has been added for ending completion or NPC quest steps.
- Current tests assert that unmapped completion evidence remains Unknown.

Evidence/source:
- `data/sekiro/endings.json`
- `docs/research/boss-flags.md`
- `docs/research/event-flags.md`

Confidence: Unknown until persistent ending/progression flags are verified from save analysis or trusted reverse-engineering sources.
