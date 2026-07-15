# Kindled Save Analyzer

Kindled is a privacy-preserving, evidence-driven game save analyzer. It reads supported save files locally in the browser and turns verified save evidence into clear progress reports.

Sekiro: Shadows Die Twice is currently supported. The architecture and normalized report model are designed to accommodate additional games over time.

## Current Capabilities

- Parses Sekiro BND4 `.sl2` save containers and extracts `USER_DATA000`.
- Reports Gourd Seeds, Prayer Beads, Prosthetic Tools and upgrades, Skills, Key Items, and Ending-route evidence.
- Preserves `unknown` when the available save evidence cannot support a definite status.
- Keeps boss detection conservative until reliable persistent completion flags are verified.
- Runs the TypeScript parser and analyzer entirely in the browser.
- Persists only the generated report and file name in browser storage so a user can return to the result.

## Repository Layout

```text
apps/web/             Astro and React browser application
packages/parser/      Save-container parsers
packages/analyzer/    Game-specific analyzers
packages/shared/      Shared utilities and report types
data/                  Source-backed game mappings
docs/PROJECT.md       Architecture, evidence model, status, and roadmap
docs/research/        Reverse-engineering notes and evidence
research/reference/   Reference implementations
research/fixtures/    Verified save fixtures
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

## Current Status

The TypeScript Sekiro implementation matches the frozen golden report for the verified fixture. Its supported categories use evidence-backed status rules. Boss completion and Ninjutsu ownership remain intentionally unresolved where reliable save evidence is not yet available.

The primary validation limitation is fixture breadth: the repository currently contains one verified fixture derived from a real save. Its Steam account identifier bytes are neutralized while the parser and analyzer evidence remains unchanged. Additional sanitized fixtures covering alternate routes, NG+, Offering Box states, and Ninjutsu states remain part of the roadmap.

For the full architecture, methodology, status model, limitations, and roadmap, see [docs/PROJECT.md](docs/PROJECT.md).

Kindled is an independent community project and is not affiliated with or endorsed by FromSoftware, Activision, or Valve. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for research-source and trademark notices.
