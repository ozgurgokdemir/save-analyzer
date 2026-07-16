# Boss Progression Flags Research

Last updated: 2026-07-16

## Current coverage

The analyzer reports progression for the 14 major bosses that award unique Memories. Each status is driven by the persistent `getItemFlagId` on that boss's `ItemLotParam` Memory reward row:

- flag ON: `defeated`
- flag OFF: `not_defeated`
- undecodable flag: `unknown`

The label describes persistent character progression: it proves that the Memory reward has been awarded on this character. It does not yet distinguish an award from the active NG cycle from one carried forward from an earlier cycle.

| Fixture | Defeated | Not defeated | Unknown |
|---|---:|---:|---:|
| Reference | 8 | 6 | 0 |
| After Divine Dragon | 9 | 5 | 0 |
| Before Sword Saint Isshin | 11 | 3 | 0 |

The reference fixture reports Gyoubu Oniwa, Lady Butterfly, Genichiro, Folding Screen Monkeys, Guardian Ape, Corrupted Monk, Great Shinobi Owl, and True Monk as defeated.

## Evidence model

Public `ItemLotParam` rows map all 14 Memory rewards to persistent event flags. Public `EquipParamGoods` rows map goods IDs `5200` through `5213` to the corresponding Memory names. The analyzer reads those flags through the verified serialized event-flag layout.

Memory inventory records remain corroborating evidence because Memories can be consumed. SoulSplitter `930x` flags also remain candidate-only evidence because controlled comparisons showed they do not provide reliable persistent character progression. Neither corroborating source overrides the Memory award flag.

The three sanitized fixtures verify that the Memory award flags advance consistently with known playthrough progression. Regression tests assert the exact defeated boss set in each fixture.

Evidence/source:

- `data/sekiro/bosses.json`
- `data/sekiro/event-flag-layout.json`
- `packages/analyzer/test/sekiro-golden.test.ts`
- `research/fixtures/README.md`
- ItemLotParam rows: https://github.com/sekiro-online/params/blob/master/src/ItemLotParam.csv
- EquipParamGoods rows: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv
- SoulSplitter boss candidates: https://github.com/FrankvdStam/SoulSplitter/blob/main/src/SoulMemory/Sekiro/Boss.cs

Confidence: Verified for persistent Memory-award progression across the three first-playthrough fixtures.

## Boundaries

- Coverage is limited to the 14 Memory-awarding major bosses. Minibosses and encounters without a unique Memory require separate progression flags.
- NG+ cycle attribution is unresolved. An ON flag proves that the character has received the reward, not necessarily that the boss was defeated in the active cycle.
- Prayer Bead locations do not depend on boss status. Their pickup, reward, replacement, and shop flags reconcile independently.