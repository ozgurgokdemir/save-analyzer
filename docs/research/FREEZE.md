# Research Freeze

Last updated: 2026-07-16

## Purpose

This document defines the stable Sekiro analyzer contract. The production TypeScript analyzer, structured mappings, sanitized fixtures, and golden report must change together whenever status semantics change.

The legacy Python analyzer remains useful for historical research context, but the production TypeScript implementation and its automated tests are authoritative for current behavior.

## Reference points

| Role | Path or command |
|---|---|
| Production parser | `packages/parser/src/index.ts` |
| Production analyzer | `packages/analyzer/src/sekiro/index.ts` |
| Analyzer regression tests | `packages/analyzer/test/sekiro-golden.test.ts` |
| Privacy tests | `packages/parser/test/fixture-privacy.test.ts` |
| Fixture conventions | `research/fixtures/README.md` |
| Golden fixture | `research/fixtures/sekiro/001/S0000.sl2` |
| Golden report | `research/reports/exact_location_report.json` |
| Structured mappings | `data/sekiro/*.json` |
| Research rationale | `docs/research/*.md` |

Run the contract checks with:

```powershell
pnpm test
pnpm build
```

## Fixture contract

All committed save fixtures are privacy-sanitized and stored as `sekiro/<fixture-id>/S0000.sl2`. Raw player saves must not be committed.

The suite contains three progression stages:

- original reference;
- after Divine Dragon;
- before Sword Saint Isshin.

The reference fixture uses active slot `USER_DATA000` and has SHA-256 `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`. See `research/fixtures/README.md` for the fixture ID and privacy conventions.

## Normalized categories and statuses

| Category | Allowed statuses |
|---|---|
| Gourd Seeds | `collected`, `missing`, `unknown` |
| Prayer Beads | `collected`, `missing`, `unknown` |
| Prosthetic Tools | `collected`, `missing`, `unknown` |
| Prosthetic Upgrades | `unlocked`, `missing`, `unknown` |
| Skills | `unlocked`, `missing`, `unknown` |
| Key Items | `collected`, `missing`, `unknown` |
| Bosses | `defeated`, `not_defeated`, `unknown` |
| Endings | `completed`, `available`, `incomplete`, `blocked`, `unknown` |

Every normalized entity preserves `id`, `name`, `category`, `status`, `confidence`, `evidence`, `acquisitionMetadata`, and `notes`. Every category summary exposes its complete status-keyed shape, including zero-count statuses.

`unknown` remains a valid defensive result when required evidence cannot be decoded or has not been mapped. It must not be removed from the analyzer model merely because a fixture currently produces zero unknowns in most categories.

## Reference fixture expectations

| Category | Expected summary |
|---|---|
| Gourd Seeds | 9 total, 7 collected, 2 missing, 0 unknown |
| Prayer Beads | 40 total, 26 collected, 14 missing, 0 unknown |
| Prosthetic Tools | 10 total, 9 collected, 1 missing, 0 unknown |
| Prosthetic Upgrades | 30 total, 12 unlocked, 18 missing, 0 unknown |
| Skills | 57 total, 31 unlocked, 26 missing, 0 unknown |
| Key Items | 33 total, 22 collected, 11 missing, 0 unknown |
| Bosses | 14 total, 8 defeated, 6 not defeated, 0 unknown |
| Endings | 4 total, 3 incomplete, 1 unknown |

Specific expectations:

- Missing Gourd Seeds: Mibu Village and Fountainhead Palace.
- Missing base Prosthetic Tool: Loaded Umbrella.
- Bloodsmoke and Puppeteer Ninjutsu are unlocked; Bestowal is missing.
- Shura is unknown; Immortal Severance, Purification, and Return are incomplete.

## Status evidence rules

- Gourd Seeds and Prayer Beads combine inventory-derived totals with verified pickup, reward, replacement, and shop flags.
- Prosthetic Tools and Upgrades use verified weapon inventory records.
- Weapon-backed Skills use verified weapon inventory records; Ninjutsu uses persistent ItemLot acquisition flags.
- Retained Key Items use inventory records; consumed, transformed, and superseded items use persistent ItemLot/Shop acquisition flags.
- The 14 Memory-awarding major bosses use persistent Memory reward ItemLot flags. This proves character progression, not active NG-cycle attribution.
- Ending status consumes Key Item evidence but requires separate completion and permanent lockout evidence.
- Community acquisition guidance is never status-driving.

## Known limitations

- Sekiro is the only supported game.
- NG+ cycle attribution is not generalized.
- Offering Box replacement behavior is not generalized.
- Boss coverage excludes minibosses and non-Memory encounters.
- Ending completion, route-choice, and detailed NPC quest-step flags remain unresolved.
- Sakura Dance row identity and some param-level skill guidance semantics remain unresolved.
- Some acquisition metadata is community-sourced guidance rather than direct save evidence.

## Rules for future changes

- Preserve valid container, privacy, and malformed-input checks.
- Add sanitized cross-fixture evidence before generalizing save semantics.
- Keep evidence separate from conclusions.
- Prefer `unknown` when required evidence is absent or undecodable.
- Do not infer ownership or progression from community guidance.
- Update mappings, tests, documentation, and the golden report together when semantics change.
- Do not commit raw player saves.