# Research Freeze

Last updated: 2026-07-09

## Purpose

This document is the contract between the Python reference implementation and the future TypeScript implementation.

After this freeze:

- Analyzer semantics should remain stable.
- New functionality should only be added by extending the analyzer, not changing verified behavior.
- The TypeScript implementation must match the Python reference output.
- The golden report is the expected output for regression testing.
- Any future semantic changes must update the tests, documentation, and golden report together.

This document is intended to be the long-term reference for contributors implementing or extending the analyzer.

## Frozen Reference Points

| Role | Path or command |
|---|---|
| Reference implementation | `research/reference/analyzer.py` |
| Reference tests | `research/reference/tests/test_analyzer.py` |
| Golden fixture | `research/fixtures/S0000.sl2` |
| Golden report | `research/reports/exact_location_report.json` |
| Structured mappings | `data/sekiro/*.json` |
| Research notes | `docs/research/*.md` |

The provided fixture is a privacy-sanitized `S0000.sl2`, the active analyzed slot is `USER_DATA000`, and the fixture SHA-256 is:

```text
478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a
```

The current golden report SHA-256 is:

```text
93F28702200A29BC6E22783F9ACFE41C15B482B2AC83215ADB5A218FA915DE27
```

## Required Commands

Run the Python reference test suite:

```powershell
python -m unittest discover -s research\reference\tests -p "test_*.py"
```

Validate the golden report and mapping JSON files:

```powershell
python -m json.tool research\reports\exact_location_report.json > $null
Get-ChildItem data\sekiro -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null }
```

Regenerate the golden report:

```powershell
python research\reference\analyzer.py > $null
```

## Repository Layout

Only the following layout is relevant to the frozen Python reference contract:

```text
data/sekiro/          Source-backed analyzer mappings
docs/PROJECT.md       Complete project documentation
docs/research/        Reverse-engineering notes and evidence
research/fixtures/    Shared save fixtures
research/reference/   Python reference implementation and tests
research/reports/     Golden analyzer outputs
```

Durable mappings belong in `data/sekiro/*.json`. Research rationale belongs in `docs/research/*.md`. The analyzer implementation belongs in `research/reference/analyzer.py`.

## Current Analyzer Coverage

The current analyzer supports Sekiro: Shadows Die Twice only.

Frozen behavior:

- Parses Sekiro BND4 `.sl2` saves.
- Extracts `USER_DATA000` from the provided fixture.
- Loads structured mappings from `data/sekiro/*.json`.
- Reads event flags using the documented base offset `0xE8000`, `eventFlag % 1000000`, and LSB-first bit order.
- Reads inventory goods and weapon records from the active slot.
- Derives Gourd Seed and Prayer Bead totals from inventory/progression records.
- Reports verified Gourd Seed and Prayer Bead locations for the current fixture.
- Reports base Prosthetic Tools and Prosthetic Tool Upgrades from inventory weapon records.
- Reports verified Skills from direct inventory weapon evidence where ownership evidence is known.
- Reports Key Items from verified inventory evidence where retention semantics are reliable.
- Reports Ending route status from Key Item analyzer results and route guidance.
- Preserves Bosses as a deferred category with unknown statuses until reliable persistent boss-completion flags are mapped.

The analyzer is intentionally conservative. `unknown` is preferred over guessing when evidence is incomplete.

## Supported Categories

`parseSekiroSaveShape` currently contains these sections:

- `inventory`
- `eventFlags`
- `bosses`
- `prayerBeads`
- `gourdSeeds`
- `prosthetics`
- `prostheticUpgrades`
- `skills`
- `keyItems`
- `endings`

`inventory` and `eventFlags` are support sections. The normalized progression categories are:

- `bosses`
- `prayerBeads`
- `gourdSeeds`
- `prosthetics`
- `prostheticUpgrades`
- `skills`
- `keyItems`
- `endings`

Each normalized progression category exposes `entities` and `summary`. Each entity should preserve the shared fields:

```json
{
  "id": "...",
  "name": "...",
  "category": "...",
  "status": "...",
  "confidence": "...",
  "evidence": [],
  "acquisitionMetadata": {},
  "notes": []
}
```

Category-specific research fields are also part of the reference output where present and must not be silently removed by a port.

## Current Status Model

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

Ending status definitions:

- `completed`: verified ending completion evidence exists.
- `available`: all verified requirements are currently satisfied and the player can choose this ending.
- `incomplete`: the route is still possible by currently verified evidence, but required items, quest steps, or progression are missing.
- `blocked`: verified evidence proves the ending can no longer be completed in the current playthrough.
- `unknown`: evidence is insufficient.

Missing required items usually produce `incomplete`, not `blocked`. `blocked` is reserved for verified permanent lockout evidence.

## Current Expected Summary for `S0000.sl2`

The TypeScript port must match the Python reference output for `research/fixtures/S0000.sl2` and `research/reports/exact_location_report.json`.

Top-level fixture facts:

| Field | Expected value |
|---|---:|
| File | `S0000.sl2` |
| Active slot | `USER_DATA000` |
| Healing Gourd uses | 8 |
| Unused Gourd Seeds | 0 |
| Gourd Seeds found | 7 |
| Gourd Seeds missing | 2 |
| Prayer Necklaces | 6 |
| Unused Prayer Beads | 2 |
| Prayer Beads found | 26 |
| Prayer Beads missing | 14 |

Normalized category summaries:

| Category | Expected summary |
|---|---|
| Gourd Seeds | 9 total, 7 collected, 2 missing, 0 unknown |
| Prayer Beads | 40 total, 26 collected, 14 missing, 0 unknown |
| Prosthetic Tools | 10 total, 9 collected, 1 missing, 0 unknown |
| Prosthetic Upgrades | 30 total, 12 unlocked, 18 missing, 0 unknown |
| Skills | 57 total, 29 unlocked, 25 missing, 3 unknown |
| Key Items | 33 total, 12 collected, 6 missing, 15 unknown |
| Bosses | 14 total, 0 defeated, 0 not_defeated, 14 unknown |
| Endings | 4 total, 0 completed, 0 available, 3 incomplete, 0 blocked, 1 unknown |

Specific current expectations:

- Missing Gourd Seeds: `sunken_valley`, `fujioka_info_broker`.
- Battlefield Memorial Mob Gourd Seed purchase is collected.
- Missing base Prosthetic Tool: `loaded_umbrella`.
- Endings: `shura` is `unknown`; `immortal_severance`, `purification`, and `return` are `incomplete`.
- Bosses remain deferred; every boss entity is `unknown`.

## Known Limitations

- The project currently has one verified save fixture.
- NG+ behavior is not fully generalized.
- Offering Box replacement behavior is not fully mapped as a general mechanic.
- Boss completion flags are unresolved.
- Ninjutsu ownership storage is unresolved.
- Ending completion flags are unresolved.
- Ending NPC quest-step flags are unresolved.
- Some acquisition metadata is probable community guidance, not verified save evidence.
- The parser is not yet ported to TypeScript.
- No production web UI exists yet.
- Sekiro is the only supported game.

## Deferred Research

Deferred work must extend the analyzer rather than reinterpret verified behavior.

Deferred areas:

- Persistent current-cycle boss defeated/not-defeated flags.
- Permanent Shura route-choice or lockout flags.
- Ending completion flags.
- Purification NPC/eavesdrop quest-step flags.
- Return Divine Child quest-step flags.
- Holy Chapter retention and consumption semantics.
- Ninjutsu ownership storage.
- Generalized NG+ behavior.
- Offering Box replacement semantics.
- Additional save fixtures covering alternate routes, NG+, Offering Box states, Ninjutsu states, and ending outcomes.

Current boss rule:

- Boss Memory inventory and Memory award ItemLot flags are comparison evidence only.
- SoulSplitter `930x` boss split flags are candidate evidence only.
- Neither source may drive `defeated` or `not_defeated` until persistent boss-completion semantics are verified.

Current skill rule:

- Skill ownership is driven by verified `inventory_weapon` evidence.
- Ownership must not be inferred from prerequisites, Esoteric Texts, bosses, vendors, route guidance, or community acquisition metadata.
- Ninjutsu identities are mapped, but ownership remains unknown until storage semantics are verified.

Current ending rule:

- Ending route status may consume Key Item analyzer evidence.
- Boss Memories must not be used as ending completion evidence.
- Missing route items produce `incomplete`, not `blocked`, unless verified permanent block evidence exists.

## Verified Data Sources

The frozen report currently uses these source classes:

- Direct read-only inspection of `research/fixtures/S0000.sl2`.
- `research/reports/exact_location_report.json`.
- `research/reference/tests/test_analyzer.py`.
- SoulSplitter Sekiro item pickup flags extracted via Yapped.
- SoulSplitter Sekiro Boss enum and splitter logic for candidate speedrun boss split flags.
- SoulsMods Paramdex field definitions for `ItemLotParam` and `ShopLineupParam`.
- `sekiro-online/params` data, including `EquipParamGoods`, `EquipParamWeapon`, `ItemLotParam`, `ShopLineupParam`, and `SkillParam`.
- PowerPyx Prayer Bead guide for human-readable Prayer Bead location and source names.
- Fextralife Skills, Skill Trees, Esoteric Text, and Endings pages for community acquisition and route guidance.

Source confidence rules:

- `verified`: confirmed by save data and source-backed mapping.
- `probable`: useful source-backed or community guidance metadata, but not direct ownership/status proof.
- `unknown`: insufficient evidence or unresolved storage semantics.

Community guidance must not be promoted to verified ownership or completion evidence unless independently verified from save data and structured mappings.

## Rules for Future Changes

Future contributors must preserve the freeze unless they are intentionally making a semantic analyzer change.

Required rules:

- Treat `research/reference/analyzer.py` as the Python reference implementation.
- Treat `research/fixtures/S0000.sl2` as the shared fixture.
- Treat `research/reports/exact_location_report.json` as the expected regression output.
- The TypeScript implementation must match the Python reference output for the fixture and golden report.
- Reuse `data/sekiro/*.json` directly where possible.
- Preserve normalized category summaries and entity shapes.
- Preserve legacy top-level report aliases unless a coordinated semantic change removes them.
- Add mappings to `data/sekiro/*.json`, not hardcoded parser branches, unless there is no reasonable data-driven representation.
- Prefer `unknown` when evidence is incomplete.
- Do not infer ownership, collection, boss completion, or ending completion from guidance-only metadata.
- Do not change verified behavior during documentation, layout-only, or porting work.

If a future semantic change is required, it must update all of the following together:

- Analyzer implementation.
- Tests.
- Relevant `docs/research/*.md` documentation.
- This freeze document if the contract changes.
- Golden report at `research/reports/exact_location_report.json`.

The golden report is the regression oracle. A changed golden report without corresponding tests and documentation is not a valid update.
