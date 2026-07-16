# Save Analyzer Project

Last updated: 2026-07-14

## Project Overview

Kindled is a local, evidence-driven game save analyzer. The browser app, shared report model, and package layout are designed to support multiple games; Sekiro: Shadows Die Twice is the currently implemented game.

The analyzer reads a `.sl2` save file, extracts the active `USER_DATA000` slot from the BND4 container, reads inventory records and event flags, and produces a normalized report for gameplay progress categories such as Gourd Seeds, Prayer Beads, Prosthetic Tools, Skills, Key Items, and Endings.

The project is intentionally conservative. A location, item, skill, or route is only reported with a firm status when the evidence is verified from save data and backed by structured mappings or trusted reverse-engineering sources. Unknown is preferred over guessing.

## Vision

Kindled is a privacy-preserving save analyzer that runs locally in the user's browser. Users can select a supported save file and receive a clear, source-backed checklist of what they have collected, what is missing, and what remains uncertain.

Reference implementations protect correctness as game support evolves. Production analyzers and any future implementations should be compared against shared fixtures and golden reports in `research/`.

## Supported Games

Currently supported:

- Sekiro: Shadows Die Twice

Additional games can be integrated through game-specific parsers, analyzers, mappings, fixtures, and report categories while reusing the shared browser interface and normalized report model.

## Goals

- Preserve 100% parser accuracy for verified Sekiro behavior.
- Keep all durable mappings in structured JSON under `data/sekiro/`.
- Keep every research finding documented under `docs/research/`.
- Use source-backed evidence only; do not guess.
- Keep parser output normalized for the shared web UI and future game integrations.
- Maintain a language-neutral reference layout for comparing future implementations.
- Parse saves locally without uploading or modifying user files.

Non-goals for the current phase:

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
│   ├── README.md
│   └── sekiro/
│       ├── 001/S0000.sl2
│       ├── 002/S0000.sl2
│       └── 003/S0000.sl2
└── reports/
    └── exact_location_report.json
```

Key roles:

- `data/sekiro/*.json` contains source-backed mappings and metadata.
- `docs/research/*.md` contains research notes, evidence, confidence levels, and unresolved behavior.
- `research/fixtures/README.md` documents the three sanitized Sekiro regression fixtures.
- `research/reports/exact_location_report.json` is the golden report for comparison tests and future ports.

## Analyzer Architecture

The production implementation is the TypeScript parser and analyzer in `packages/parser` and `packages/analyzer`. TypeScript golden-parity and cross-fixture tests protect the behavior contract.

High-level flow:

1. Read the BND4 `.sl2` save container.
2. Extract `USER_DATA000`.
3. Load structured mappings from `data/sekiro/*.json`.
4. Read event flags using the verified record-1000 serialized page layout.
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

Release checks:

```powershell
pnpm test
pnpm typecheck
pnpm build
```

After an intentional behavior or mapping change, regenerate the golden report with:

```powershell
pnpm golden:sekiro
```

Expected discipline:

- Add durable mappings to `data/sekiro/*.json` rather than hardcoded UI branches.
- Update the matching `docs/research/*.md` page for every verified discovery.
- Add cross-fixture assertions for every newly verified status rule.
- Update `research/fixtures/README.md` when fixtures change.
- Keep `unknown` for undecodable or genuinely unresolved evidence.
- Never commit unsanitized player saves.

## Research Methodology

Every verified finding should include:

- What was discovered.
- How it was verified.
- Evidence or source.
- Confidence: `Verified`, `Probable`, or `Unknown`.

Trusted source types currently used:

- Direct read-only analysis of the sanitized fixtures documented in `research/fixtures/README.md`.
- SoulSplitter event flag and item pickup references.
- Paramdex field definitions.
- sekiro-online param CSVs such as `SkillParam`, `EquipParamGoods`, `EquipParamWeapon`, `ItemLotParam`, and `ShopLineupParam`.
- Community guides only for human-readable location/acquisition guidance, unless independently verified.

Confidence rules:

- `verified`: confirmed by save data and source-backed mapping.
- `probable`: useful source-backed metadata, but not direct ownership/status proof.
- `unknown`: insufficient evidence or unresolved storage semantics.

## Current Progress

Three sanitized Sekiro fixtures cover the original reference stage, After Divine Dragon, and Before Sword Saint Isshin. Together they verify container parsing, the serialized event-flag decoder, and progression changes across the report.

Verified categories:

- Gourd Seeds and Prayer Beads reconcile aggregate totals with exact persistent location evidence.
- Prosthetic Tools and upgrades use verified weapon inventory records.
- Weapon-backed Skills use inventory evidence; Ninjutsu uses verified ItemLot acquisition flags.
- Key Items combine retained inventory with persistent ItemLot/Shop acquisition flags.
- Endings consume Key Item evidence and distinguish incomplete from blocked or unknown.
- Bosses report progression for all 14 Memory-awarding major bosses using persistent Memory reward flags.

Reference fixture summary:

- Gourd Seeds: `7 / 9`
- Prayer Beads: `26 / 40`
- Base Prosthetic Tools: `9 / 10`
- Prosthetic Upgrades: `12 / 30`
- Skills: `31 / 57`, `0 unknown`
- Key Items: `22 / 33`, `0 unknown`
- Bosses: `8 / 14`, `0 unknown`
- Endings: Immortal Severance incomplete, Purification incomplete, Return incomplete, Shura unknown

## Supported Analyzer Categories

Inventory and event flags are support sections used by the normalized categories below.

- **Gourd Seeds:** inventory-derived totals plus pickup and shop flags.
- **Prayer Beads:** inventory/progression totals plus pickup, reward, replacement, and shop flags.
- **Prosthetic Tools:** base `EquipParamWeapon` inventory records.
- **Prosthetic Upgrades:** upgrade `EquipParamWeapon` inventory records.
- **Skills:** verified weapon records and Ninjutsu ItemLot acquisition flags. Prerequisites and community guidance do not infer ownership.
- **Key Items:** retained goods inventory plus persistent ItemLot/Shop acquisition flags for consumed or transformed items.
- **Endings:** separate completion, availability, missing requirement, and permanent block evidence.
- **Bosses:** persistent Memory reward flags for 14 Memory-awarding major bosses; inventory and speedrun split flags remain corroborating evidence.

## Boss Coverage Boundaries

Boss status represents persistent character progression for the 14 bosses with unique Memory rewards. It does not cover minibosses or encounters without a Memory, and it does not yet attribute an ON reward flag to the active NG cycle rather than an earlier cycle.

SoulSplitter `930x` candidate flags and Memory inventory records remain useful corroborating evidence but do not override the persistent Memory reward flag.

## Current Limitations

- Sekiro is the only supported game.
- NG+ cycle attribution is not fully generalized.
- Offering Box replacement behavior is not generalized.
- Boss coverage excludes minibosses and non-Memory encounters.
- Ending completion, route-choice, and detailed NPC quest-step flags remain unresolved.
- Sakura Dance row identity and some param-level guidance semantics remain unresolved.
- Some acquisition metadata is community guidance rather than direct status evidence.
- Browser-level interaction regression coverage is not yet automated.

## Browser Web App

The Astro and React web app is implemented in `apps/web`. It imports the shared parser and analyzer packages plus each game's structured mappings and performs analysis in the browser without an upload endpoint.

Release checks:

```powershell
pnpm test
pnpm typecheck
pnpm build
```

Web app behavior:

- Parses supported saves locally in the browser.
- Never uploads or mutates user saves.
- Stores the generated report and selected file name in browser storage for return visits.
- Presents verified statuses and unknowns separately.
- Exposes acquisition guidance while hiding internal mapping identifiers.

## Roadmap

1. Add independently sourced fixtures for alternate routes, ending outcomes, NG+, Offering Box states, and multiple active slots.
2. Add browser-level tests for file selection, analysis, category navigation, persistence, reset, and error handling.
3. Add a defensive file-size limit and evaluate moving parsing off the main browser thread.
4. Add and verify production security headers.
5. Extend boss coverage to non-Memory encounters when reliable persistent evidence is available.
6. Add more games after the shared parser, analyzer, and report contracts are stable enough to support them cleanly.