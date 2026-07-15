# Sekiro Reference Analyzer

This directory contains the reference implementation used to verify Sekiro save parsing behavior before and during ports to other runtimes.

The implementation is currently written in Python, but this directory is organized by role, not language: future TypeScript, Rust, or other implementations should be compared against the shared fixture and golden report under `research/`.

## Layout

- `analyzer.py` parses the BND4 `.sl2` container, extracts `USER_DATA000`, loads mappings from `../../data/sekiro`, and writes the normalized exact-location report.
- `tests/` contains the reference behavior tests.
- `../fixtures/S0000.sl2` is the shared read-only, privacy-sanitized Sekiro save fixture. Steam account identifier bytes are neutralized without changing analyzer evidence.
- `../reports/exact_location_report.json` is the shared golden report for implementation comparisons.

## Commands

Regenerate the golden report:

```powershell
python research\reference\analyzer.py > $null
```

Run the reference test suite:

```powershell
python -m unittest discover -s research\reference\tests -p "test_*.py"
```

The analyzer must not modify the save fixture. Durable mappings belong in `data/sekiro/*.json`, and research notes belong in `docs/research/*.md`.
