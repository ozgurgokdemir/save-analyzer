# Save Analyzer

Save Analyzer is a local, evidence-driven save parser for FromSoftware games. The project currently supports Sekiro: Shadows Die Twice through a Python reference implementation and source-backed JSON mappings.

The analyzer reads a Sekiro `.sl2` save, extracts `USER_DATA000`, evaluates inventory records and event flags, and emits a normalized report for verified progression categories.

## Current Capabilities

- Parses Sekiro BND4 `.sl2` saves.
- Extracts `USER_DATA000`.
- Reads documented event flags using the `0xE8000` layout.
- Detects inventory-derived Gourd Seed and Prayer Bead totals.
- Reports verified Gourd Seed and Prayer Bead locations for the current fixture.
- Reports Prosthetic Tools and Prosthetic Tool Upgrades from inventory weapon records.
- Reports verified Skills where ownership evidence is known.
- Reports Key Items and Ending route availability through verified item evidence.
- Keeps Bosses deferred until reliable persistent boss-completion flags are found.

## Repository Layout

```text
data/sekiro/          Source-backed analyzer mappings
docs/PROJECT.md       Complete project documentation
docs/research/        Reverse-engineering notes and evidence
research/fixtures/    Shared save fixtures
research/reference/   Reference implementation and tests
research/reports/     Golden analyzer outputs
```

## Quick Start

Regenerate the golden report:

```powershell
python research\reference\analyzer.py > $null
```

Run the reference test suite:

```powershell
python -m unittest discover -s research\reference\tests -p "test_*.py"
```

Validate JSON files:

```powershell
python -m json.tool research\reports\exact_location_report.json > $null
Get-ChildItem data\sekiro -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null }
```

## Current Status

The reference analyzer is stable for the verified Sekiro fixture. Gourd Seeds, Prayer Beads, Prosthetics, Prosthetic Upgrades, many Skills, Key Items, and Endings are implemented with evidence-backed status rules. Bosses and Ninjutsu ownership remain intentionally unresolved where reliable save evidence is not yet available.

For full architecture, methodology, status models, progress, limitations, and roadmap, see [docs/PROJECT.md](docs/PROJECT.md).
