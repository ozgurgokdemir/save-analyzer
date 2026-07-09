# Save Analyzer Project

Last updated: 2026-07-09

## Project Overview

Save Analyzer is a local, evidence-driven save parser for FromSoftware save files. The current project focuses on Sekiro: Shadows Die Twice and uses a Python reference implementation to verify parser behavior before porting the analyzer to TypeScript and building a browser-based web app.

The analyzer reads a `.sl2` save file, extracts the active `USER_DATA000` slot from the BND4 container, reads inventory records and event flags, and produces a normalized report for gameplay progress categories such as Gourd Seeds, Prayer Beads, Prosthetic Tools, Skills, Key Items, and Endings.

The project is intentionally conservative. A location, item, skill, or route is only reported with a firm status when the evidence is verified from save data and backed by structured mappings or trusted reverse-engineering sources. Unknown is preferred over guessing.

## Vision

The long-term goal is a privacy-preserving save analyzer that runs locally in the user's browser. Users should be able to select a save file and receive a clear, source-backed checklist of what they have collected, what is missing, and what remains uncertain.

The reference implementation exists to protect correctness while the project moves toward production. Future implementations, including TypeScript and possibly Rust, should be compared against the shared fixture and golden report in `research/`.

## Supported Games

Currently supported:

- Sekiro: Shadows Die Twice

Not yet supported:

- Dark Souls
- Dark Souls II
- Dark Souls III
- Bloodborne
- Elden Ring
- Other FromSoftware titles

The repository structure is intended to support future games, but Sekiro is the only game with verified mappings today.

## Goals

- Preserve 100% parser accuracy for verified Sekiro behavior.
- Keep all durable mappings in structured JSON under `data/sekiro/`.
- Keep every research finding documented under `docs/research/`.
- Use source-backed evidence only; do not guess.
- Keep parser output normalized enough for a future web UI.
- Maintain a language-neutral reference layout for comparing future implementations.
- Parse saves locally without uploading or modifying user files.

Non-goals for the current phase:

- Building UI before the parser is reliable.
- Treating boss Memory inventory as boss defeat proof.
- Inferring ownership from prerequisites, route guidance, or community text alone.

## Repository Structure

```text
data/
└── sekiro/
    ├── bosses.json
    ├── endings.json
    ├── event-flag-layout.json
    ├── gourd-seeds.json
    ├── item-ids.json
    ├── key-items.json
    ├── prayer-beads.json
    ├── prosthetics.json
    ├── prosthetic-upgrades.json
    └── skills.json

docs/
├── PROJECT.md
└── research/
    ├── boss-flags.md
    ├── endings.md
    ├── event-flags.md
    ├── gourd-seeds.md
    ├── item-lots.md
    ├── key-items.md
    ├── prayer-beads.md
    ├── prosthetics.md
    ├── save-format.md
    ├── skills.md
    └── status-model.md

research/
├── fixtures/
│   └── S0000.sl2
├── reference/
│   ├── analyzer.py
│   ├── README.md
│   └── tests/
│       └── test_analyzer.py
└── reports/
    └── exact_location_report.json
```

Key roles:

- `data/sekiro/*.json` contains source-backed mappings and metadata.
- `docs/research/*.md` contains research notes, evidence, confidence levels, and unresolved behavior.
- `research/reference/analyzer.py` is the reference implementation.
- `research/fixtures/S0000.sl2` is the shared verified Sekiro save fixture.
- `research/reports/exact_location_report.json` is the golden report for comparison tests and future ports.

## Analyzer Architecture

The current analyzer is the Python reference implementation in `research/reference/analyzer.py`.

High-level flow:

1. Read the BND4 `.sl2` save container.
2. Extract `USER_DATA000`.
3. Load structured mappings from `data/sekiro/*.json`.
4. Read event flags using the documented `0xE8000` layout.
5. Read inventory and weapon records from the slot.
6. Evaluate evidence rules for each mapped entity.
7. Emit normalized category entities and summaries.
8. Write the golden report to `research/reports/exact_location_report.json`.

Current normalized categories include:

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

Each mapped entity is shaped around common fields where possible:

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

The project does not force every category into identical statuses. Statuses are domain-specific so the API remains clear.

## Status Model

Prayer Beads:

- `collected`
- `missing`
- `unknown`

Gourd Seeds:

- `collected`
- `missing`
- `unknown`

Prosthetic Tools:

- `collected`
- `missing`
- `unknown`

Prosthetic Upgrades:

- `unlocked`
- `missing`
- `unknown`

Skills:

- `unlocked`
- `missing`
- `unknown`

Bosses:

- `defeated`
- `not_defeated`
- `unknown`

Endings:

- `completed`
- `available`
- `incomplete`
- `blocked`
- `unknown`

Ending definitions:

- `completed`: verified ending completion evidence exists.
- `available`: all verified requirements are currently satisfied and the player can choose the ending.
- `incomplete`: the route is still possible, but required items, quest steps, or progression are missing.
- `blocked`: verified permanent block evidence exists.
- `unknown`: evidence is insufficient.

Missing required items usually produce `incomplete`, not `blocked`.

## Development Workflow

Reference commands:

```powershell
python research\reference\analyzer.py > $null
python -m unittest discover -s research\reference\tests -p "test_*.py"
```

JSON validation:

```powershell
python -m json.tool research\reports\exact_location_report.json > $null
Get-ChildItem data\sekiro -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null }
```

Expected discipline:

- Add mappings to `data/sekiro/*.json`, not hardcoded parser branches.
- Update the matching `docs/research/*.md` file for every verified discovery.
- Add tests for every newly verified mapping or status rule.
- Regenerate the golden report after behavior-affecting mapping changes.
- Prefer `unknown` when evidence is incomplete.
- Do not change parser semantics during documentation or layout-only work.

The current golden report SHA-256 is:

```text
978E04A505A9EF2998E2B211700C33D796CBCA99D28E6E89217C59FE35B5867D
```

## Research Methodology

Every verified finding should include:

- What was discovered.
- How it was verified.
- Evidence or source.
- Confidence: `Verified`, `Probable`, or `Unknown`.

Trusted source types currently used:

- Direct reads from `S0000.sl2`.
- SoulSplitter event flag and item pickup references.
- Paramdex field definitions.
- sekiro-online param CSVs such as `SkillParam`, `EquipParamGoods`, `EquipParamWeapon`, `ItemLotParam`, and `ShopLineupParam`.
- Community guides only for human-readable location/acquisition guidance, unless independently verified.

Confidence rules:

- `verified`: confirmed by save data and source-backed mapping.
- `probable`: useful source-backed metadata, but not direct ownership/status proof.
- `unknown`: insufficient evidence or unresolved storage semantics.

## Current Progress

The current fixture is `research/fixtures/S0000.sl2`. It is a valid Sekiro BND4 save, and `USER_DATA000` is the active analyzed slot.

Verified categories:

- Gourd Seeds are fully mapped for the current save.
- Prayer Beads are fully reconciled for the current save.
- Base Prosthetic Tools are verified from inventory weapon records.
- Prosthetic Tool Upgrades are verified from inventory weapon records.
- Combat Arts, passive/latent skills, martial arts, and special skills are verified where direct skill weapon records exist.
- Ninjutsu identities are mapped, but ownership is unknown.
- Key Items are implemented from verified inventory evidence where retention semantics are known.
- Endings consume Key Item analyzer results and distinguish incomplete from blocked.
- Bosses are intentionally deferred because current candidate flags are not reliable persistent boss-completion evidence.

Current fixture summary:

- Gourd Seeds: `7 / 9`
- Prayer Beads: `26 / 40`
- Base Prosthetic Tools: `9 / 10`
- Prosthetic Upgrades: `12 / 30`
- Skills: `57 total`, `29 unlocked`, `25 missing`, `3 unknown`
- Endings: Immortal Severance incomplete, Purification incomplete, Return incomplete, Shura unknown
- Bosses: deferred; statuses remain unknown unless a verified persistent progression flag is found

## Supported Analyzer Categories

Inventory:

- Reads known goods quantities and progression-derived totals.

Event Flags:

- Uses the documented `0xE8000` layout.
- Supports low item flags, shop flags, Prayer Bead secondary flags, and known candidate split flags as research-only where appropriate.

Gourd Seeds:

- Uses inventory totals plus item pickup and shop purchase flags.
- Current verified missing locations are Sunken Valley and Fujioka the Info Broker.
- Battlefield Memorial Mob is verified collected.

Prayer Beads:

- Uses inventory/progression total, primary pickup/shop flags, secondary ItemLotParam reward flags, and shop evidence.
- Current fixture has `26 collected`, `14 missing`, `0 unknown`.

Prosthetic Tools:

- Uses base `EquipParamWeapon` inventory records.
- Current fixture is missing Loaded Umbrella.

Prosthetic Upgrades:

- Uses upgrade `EquipParamWeapon` inventory records.
- Upgrades are treated separately from base tools.

Skills:

- Uses direct `inventory_weapon` evidence for verified SkillParam and EquipParamWeapon rows.
- Does not infer ownership from prerequisites, Esoteric Texts, bosses, or acquisition guidance.
- Ninjutsu goods rows are identified but ownership storage is unresolved.

Key Items:

- Uses verified inventory evidence where item retention semantics are reliable.
- Supports ending route analysis.

Endings:

- Uses completion, availability, missing requirement, and block evidence separately.
- Does not infer endings from boss Memories.

Bosses:

- Category exists but remains deferred.
- Boss Memory items and Memory award ItemLot flags are comparison evidence only, not defeat proof.

## Deferred Work: Bosses

Boss analysis is deferred because the investigated candidates are not reliable current-playthrough completion signals.

Known facts from user verification and save research:

- Genichiro was defeated, but candidate speedrun split flag `9303` reads OFF.
- Isshin Ashina was not defeated, and candidate flag `9316` reads OFF.
- Headless Ape was uncertain, and candidate flag `9307` reads ON.

Conclusion:

- `930x` SoulSplitter-style boss split flags must not drive `defeated` or `not_defeated`.
- Memory inventory and Memory award ItemLot flags must not drive boss defeat status.
- Boss statuses should remain `unknown` until verified persistent boss/progression flags are found.

## Current Limitations

- The project currently has one verified save fixture.
- NG+ behavior is not fully generalized.
- Offering Box replacement behavior is not fully mapped as a general mechanic.
- Boss completion flags are unresolved.
- Ninjutsu ownership storage is unresolved.
- Some acquisition metadata is probable community guidance, not verified save evidence.
- The parser is not yet ported to TypeScript.
- No production web UI exists yet.
- Sekiro is the only supported game.

## Next Phase: TypeScript and Web App

The next phase is to port the analyzer to TypeScript while preserving behavior against the reference implementation.

Porting expectations:

- Treat `research/reference/analyzer.py` as the reference implementation.
- Treat `research/fixtures/S0000.sl2` as the shared fixture.
- Treat `research/reports/exact_location_report.json` as the golden output.
- Reuse `data/sekiro/*.json` directly.
- Match the normalized entity model and category summaries.
- Add TypeScript tests that compare output against the golden report.
- Only after parity is reached, build the web app UI.

Web app expectations:

- Parse saves locally in the browser.
- Never upload or mutate user saves.
- Present verified statuses clearly.
- Show unknowns honestly.
- Link UI rows back to evidence and acquisition metadata.

## Roadmap

1. Keep the Python reference implementation stable.
2. Create the TypeScript parser and analyzer.
3. Build parity tests against `research/reports/exact_location_report.json`.
4. Validate TypeScript output against the reference fixture.
5. Add a browser file picker and local parsing pipeline.
6. Build checklist views for verified categories.
7. Add evidence detail views for advanced users.
8. Continue boss flag research when reliable sources or additional test saves are available.
9. Add more save fixtures to cover alternate routes, NG+, Offering Box states, and Ninjutsu states.
10. Consider future support for other FromSoftware games once Sekiro is stable.
