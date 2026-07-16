# Analyzer Status Model

Last updated: 2026-07-16

## Finalized category statuses

What was discovered:
- The analyzer should use domain-specific statuses per category instead of forcing every category into one generic enum.
- Evidence should remain separate from status. A status is a conclusion produced from evidence and category policy, not the evidence itself.
- Missing route requirements for endings usually mean `incomplete`, not `blocked`.
- `blocked` is reserved for verified permanent lockout evidence.

| Category | Allowed statuses |
|---|---|
| Prayer Beads | `collected`, `missing`, `unknown` |
| Gourd Seeds | `collected`, `missing`, `unknown` |
| Prosthetic Tools | `collected`, `missing`, `unknown` |
| Prosthetic Upgrades | `unlocked`, `missing`, `unknown` |
| Skills | `unlocked`, `missing`, `unknown` |
| Key Items | `collected`, `missing`, `unknown` |
| Bosses | `defeated`, `not_defeated`, `unknown` |
| Endings | `completed`, `available`, `incomplete`, `blocked`, `unknown` |

How it was verified:
- Existing parser categories were reviewed against their current status rules and tests.
- Gourd Seeds, Prayer Beads, Prosthetic Tools, Prosthetic Upgrades, Skills, Key Items, and Bosses already use category-specific status sets in current save output.
- Prayer Beads no longer expose `unresolved` as a location status; unresolved evidence paths collapse to `unknown`.
- Endings were refined so missing required items produce `incomplete`; `blocked` requires verified permanent block evidence.
- Key Items use verified retained inventory evidence plus persistent ItemLot/Shop acquisition flags for consumed or transformed items; acquisition guidance remains non-driving.

Evidence/source:
- `packages/analyzer/src/sekiro/index.ts`
- `packages/analyzer/test/sekiro-golden.test.ts`
- `data/sekiro/endings.json`
- `data/sekiro/key-items.json`
- `docs/research/endings.md`
- `docs/research/key-items.md`

Confidence: Verified for implemented parser status outputs across the three sanitized fixtures. Unknown remains the defensive result for undecodable evidence and unresolved ending state.

## Normalized report schema

What was discovered:
- Every normalized progression category now exposes an `entities` array and `summary` for future parser/API consumers.
- `inventory` and `eventFlags` are support sections in `parseSekiroSaveShape`, not normalized entity categories, so they intentionally do not expose `entities` or `summary`.
- Existing category-specific outputs such as `gourdSeeds.locations`, `prayerBeads.locations`, and ending `completionEvidence` / `availabilityEvidence` are preserved for research traceability.
- Every entity in the normalized arrays carries these common fields: `id`, `name`, `category`, `status`, `confidence`, `evidence`, `acquisitionMetadata`, and `notes`.
- Every category summary now includes `total`, one count for each allowed status, and `byStatus` using the exact domain status keys.
- Boss summaries keep the legacy `notDefeated` alias, but the normalized status-keyed summary uses `not_defeated`.
- Key Items keep `ownershipEvidence` and `acquisitionEvidence` for readability, and also expose those records through generic `evidence`.
- Endings keep `completionEvidence`, `availabilityEvidence`, `missingRequirements`, and `blockEvidence`, and also expose a combined generic `evidence` list.
- Generic evidence entries always carry `id`, `state`, `status`, and `confidence`. Most evidence entries also carry a `type`; ending `blockEvidence` entries intentionally preserve their rule shape (`when`, `conditionEvidence`, `statusDriving`, and `blockType`) and are included in the combined `evidence` list without inventing a new analyzer semantic.
- The top-level legacy report aliases `gourd_seed_locations`, `gourd_seed_summary`, `prayer_bead_sample_flags`, `boss_memory_items_found`, `derived_counts`, `event_flag_reader`, `sources_used`, and `limitations` are intentionally preserved around `parseSekiroSaveShape` for research continuity.

How it was verified:
- Added automated tests that require every normalized progression category to have `entities` and `summary.byStatus`.
- Added tests that distinguish normalized progression categories from support sections.
- Added tests that require every entity to contain the shared fields listed above.
- Added tests that require each summary count to match the entity statuses.
- Added tests that require `verified` entity statuses to be backed by non-empty evidence.
- Added tests that require generic evidence entries to expose the common evidence fields and require ending-specific evidence fields to remain compatible with the generic model.
- Added tests that require legacy top-level report aliases to remain intentionally preserved.
- Added JSON mapping validation tests and ID uniqueness checks for every structured mapping file.
- Added ending reference tests requiring `data/sekiro/endings.json` to use `key_item` references instead of duplicated raw `inventory_item` route evidence.
- Added tests that prevent community-only acquisition guidance from being marked `Verified`.

Evidence/source:
- `packages/analyzer/src/sekiro/index.ts`
- `packages/analyzer/test/sekiro-golden.test.ts`
- `research/reports/exact_location_report.json`
- `data/sekiro/*.json`

Confidence: Verified for current parser output, mapping-file validation, and cross-fixture regression coverage.

## Endings status definitions

What was discovered:
- `completed` means verified ending completion evidence exists.
- `available` means all verified requirements are currently satisfied and the player can choose this ending.
- `incomplete` means the ending route is still possible by currently verified evidence, but required items, quest steps, or progression are missing.
- `blocked` means verified evidence proves the ending can no longer be completed in the current playthrough.
- `unknown` means evidence is insufficient, including cases where potential block evidence exists but is not verified as permanent.

How it was verified:
- The current save lacks verified ending completion flags, so no ending is `completed`.
- The current save lacks `Divine Dragon's Tears`, so non-Shura endings are not `available`.
- Immortal Severance, Purification, and Return have missing required items and no verified permanent block evidence, so they are `incomplete`.
- Shura has probable block evidence from `Aromatic Branch`, but no verified permanent route-choice flag, so it remains `unknown` rather than `blocked`.

Evidence/source:
- `data/sekiro/endings.json`
- `docs/research/endings.md`
- Fextralife Endings route guidance: https://sekiroshadowsdietwice.wiki.fextralife.com/Endings
- sekiro-online EquipParamGoods row data: https://github.com/sekiro-online/params/blob/master/src/EquipParamGoods.csv

Confidence: Verified for status logic behavior in tests. Probable for community route guidance. Unknown for true ending completion and route-choice event flags until mapped.
