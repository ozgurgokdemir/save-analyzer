# Kindled Save Analyzer

Kindled is a privacy-preserving, evidence-driven game save analyzer. It reads supported save files locally in the browser and turns verified save evidence into clear progress reports.

Sekiro: Shadows Die Twice is currently supported. The architecture and normalized report model are designed to accommodate additional games over time.

## Current capabilities

- Parses Sekiro BND4 `.sl2` save containers and extracts `USER_DATA000`.
- Reports exact Gourd Seed and Prayer Bead locations.
- Reports Prosthetic Tools and upgrades, Skills including Ninjutsu, Key Items, ending-route evidence, and progression for 14 Memory-awarding major bosses.
- Preserves `unknown` when required evidence cannot be decoded or has not been mapped.
- Runs the TypeScript parser and analyzer entirely in the browser.
- Persists only the generated report and file name in browser storage.

## Repository layout

```text
apps/web/             Astro and React browser application
packages/parser/      Save-container parsers
packages/analyzer/    Game-specific analyzers
packages/shared/      Shared utilities and report types
data/                  Source-backed game mappings
docs/PROJECT.md       Architecture, evidence model, status, and roadmap
docs/research/        Reverse-engineering notes and evidence
research/fixtures/    Sanitized regression fixtures
research/reports/     Frozen golden analyzer output
```

## Development

Install dependencies and start the web app:

```powershell
pnpm install
pnpm --filter @save-analyzer/web dev
```

Run the release checks:

```powershell
pnpm test
pnpm typecheck
pnpm build
```

Regenerate the reference golden report after an intentional analyzer or mapping change:

```powershell
pnpm golden:sekiro
```

## Current status

The production TypeScript analyzer is regression-tested against three privacy-sanitized progression stages: the original reference, After Divine Dragon, and Before Sword Saint Isshin. These fixtures cover the event-flag decoder, exact collectible locations, boss progression, Ninjutsu, and acquisition-backed Key Items.

The main remaining evidence gaps are ending completion/route-choice flags, NG+ cycle attribution, generalized Offering Box behavior, non-Memory bosses, and Sakura Dance row identity. See [docs/PROJECT.md](docs/PROJECT.md) and [research/fixtures/README.md](research/fixtures/README.md) for details.

Kindled is an independent community project and is not affiliated with or endorsed by FromSoftware, Activision, or Valve. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for research-source and trademark notices.