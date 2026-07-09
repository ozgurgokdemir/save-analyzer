# Boss Flags Research

Last updated: 2026-07-08

## Current boss coverage

What was discovered:
- Bosses now use the generic evidence model.
- Public ItemLotParam row data maps 14 boss Memory award rows to event flags.
- Public EquipParamGoods row data confirms goods IDs `5200` through `5213` are boss Memories.
- In `S0000.sl2`, 12 boss Memory award flags are ON and 2 are OFF.
- User verification confirms this save is a first playthrough.
- User verification confirms `genichiro` was defeated, but candidate flag `9303` reads OFF.
- User verification confirms `isshin_ashina` was not defeated, and candidate flag `9316` reads OFF.
- User verification no longer treats `headless_ape` as a hard negative; it may have been defeated, and candidate flag `9307` reads ON.
- Therefore Memory inventory and Memory award ItemLot flags are comparison evidence only.
- SoulSplitter source maps Sekiro boss split enum values `9301` through `9317`, and its splitter reads Boss split values as event flags.
- These SoulSplitter flags are now recorded as `speedrunSplitFlagCandidate` evidence only.
- SoulSplitter `930x` flags are not reliable persistent boss-completion evidence in this save and do not drive `defeated` or `not_defeated`.
- The parser still marks all bosses as `unknown` until a verified boss defeat/progression flag with current-cycle completion semantics is mapped.

| Boss | Memory flag | Memory state | Candidate split flag | Candidate state | Status | Confidence |
|---|---:|---|---:|---|---|---|
| Gyoubu Oniwa | 50002001 | ON | 9301 | ON | unknown | unknown |
| Lady Butterfly | 50002031 | ON | 9302 | ON | unknown | unknown |
| Genichiro | 50002081 | ON | 9303 | OFF | unknown | unknown |
| Folding Screen Monkeys | 50002021 | ON | 9305 | ON | unknown | unknown |
| Guardian Ape | 50002011 | ON | 9304 | ON | unknown | unknown |
| Corrupted Monk | 50002051 | ON | 9306 | ON | unknown | unknown |
| Great Shinobi Owl | 50002091 | ON | 9308 | ON | unknown | unknown |
| Owl (Father) | 50002101 | ON | 9317 | ON | unknown | unknown |
| True Monk | 50002061 | OFF | 9309 | ON | unknown | unknown |
| Divine Dragon | 50002071 | OFF | 9310 | ON | unknown | unknown |
| Demon of Hatred | 50002041 | ON | 9313 | ON | unknown | unknown |
| Sword Saint Isshin | 50002131 | ON | 9312 | OFF | unknown | unknown |
| Isshin Ashina | 50002121 | ON | 9316 | OFF | unknown | unknown |
| Headless Ape | 50002017 | ON | 9307 | ON | unknown | unknown |

How it was verified:
- Queried public `EquipParamGoods.csv` rows `5200` through `5213` to confirm the Memory names.
- Queried public `ItemLotParam.csv` rows that award goods IDs `5200` through `5213`; each row has a `getItemFlagId`.
- Read those event flags from `USER_DATA000` using the documented `0xE8000` event flag layout.
- Applied the user-verified first-playthrough facts that Genichiro was defeated while candidate flag `9303` is OFF, Isshin Ashina was not defeated while candidate flag `9316` is OFF, and Headless Ape is uncertain while candidate flag `9307` is ON.
- Read SoulSplitter `src/SoulMemory/Sekiro/Boss.cs`, `src/SoulSplitter/Splits/Sekiro/Split.cs`, and `src/SoulSplitter/Splitters/SekiroSplitter.cs`; Boss enum values are used as event flags for live boss splits.
- Read the candidate split flags from `USER_DATA000` with the documented save flag layout.
- Consistency concern: Genichiro candidate flag `9303` reads OFF despite the user-verified defeated fact, so the `930x` split flags are not reliable persistent save boss-completion flags.
- Consistency note: Isshin Ashina candidate flag `9316` is OFF and Headless Ape candidate flag `9307` is ON, but neither state is used to infer boss completion.
- Added automated tests for all 14 boss Memory award flags, inventory-memory comparison signals, candidate SoulSplitter split flags, summary counts, and the regression that candidate/memory evidence cannot produce defeated status.

Evidence/source:
- `data/sekiro/bosses.json`
- `research/reports/exact_location_report.json`
- `research/reference/tests/test_analyzer.py`
- ItemLotParam row data: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- SoulSplitter Boss enum: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulMemory/Sekiro/Boss.cs
- SoulSplitter Sekiro split model: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulSplitter/Splits/Sekiro/Split.cs
- SoulSplitter Sekiro splitter logic: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulSplitter/Splitters/SekiroSplitter.cs

Confidence: Verified that Memory evidence and SoulSplitter `930x` candidate flags are insufficient for boss defeated/not-defeated status in this save. Unknown for persistent save boss defeated/not-defeated status until true current-cycle defeat/progression flags are mapped.

## Boss defeated flags

What was discovered:
- No separate EMEVD boss-defeated flags have been verified yet.
- Memory item presence is kept as a secondary comparison signal, but it is not used alone as verified boss completion logic.
- Candidate SoulSplitter speedrun split flags are stored as evidence but are not `bossDefeatFlag` evidence.
- No current verified boss status source exists.
- A boss can be marked `defeated` only with a verified boss defeat/progression flag.
- A boss can be marked `not_defeated` only when a verified current-cycle boss completion flag is OFF.
- Prayer Bead miniboss/boss-drop locations now expose a `bossDefeatFlag` evidence slot in the parser report, but the slot is Unknown until a source-backed defeat flag mapping is added.
- Current Prayer Bead reconciliation does not infer miniboss defeats from OFF pickup/item-lot flags.
- The 11 collected-but-unattributed Prayer Beads in `S0000.sl2` are now attributed through verified secondary ItemLotParam reward/replacement flags, not through boss defeat flags.
- The 14 remaining Prayer Beads are now missing by verified item-lot/shop evidence, not through boss defeat flags.

How it was verified:
- No source-backed EMEVD boss-defeated flag table has been added.
- `S0000.sl2` has 26 inventory-derived Prayer Beads but only 15 ON primary Prayer Bead pickup/shop flags.
- Secondary ItemLotParam flags reconcile the 11-bead gap, while `bossDefeatFlag` remains Unknown in the parser output.
- Missing-by-evidence rows use OFF primary reward/pickup or shop-purchase flags plus OFF paired secondary ItemLotParam flags where applicable.
- Boss Memory award flags are separate generic boss evidence and are not reused as Prayer Bead miniboss defeat flags.
- SoulSplitter `930x` boss split flags are separate candidate generic boss evidence and are not reused as verified boss defeat flags.

Evidence/source:
- `data/sekiro/bosses.json`
- `research/reports/exact_location_report.json`
- `docs/research/item-lots.md`
- SoulSplitter Boss enum and splitter source files linked above.

Confidence: Unknown for separate boss-defeat flags; Verified that current Prayer Bead collected/missing reconciliation does not depend on boss-defeat flags.
