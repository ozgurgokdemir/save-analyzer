# Save Format Research

Last updated: 2026-07-07

## BND4 container

What was discovered:
- The privacy-sanitized `S0000.sl2` preserves a valid BND4 container structure.
- It contains 12 entries named `USER_DATA000` through `USER_DATA011`.
- `USER_DATA000` is the populated active slot for the provided save.

How it was verified:
- Parsed the BND4 entry table from the provided `S0000.sl2`.
- Re-ran `packages/analyzer/src/sekiro/index.ts` after moving mappings to JSON data files.

Evidence/source:
- Save fixture: `research/fixtures/sekiro/001/S0000.sl2`
- SHA-256: `478bab165139cb4e5a5972ba6f52aeeba024aa10ca0226751f85a8a6e1905c7a`
- Privacy treatment: SteamID64-range account identifier values are replaced with neutral bytes; parser and analyzer evidence is unchanged.
- Generated report: `research/reports/exact_location_report.json`

Confidence: Verified

## Active slot inventory counts

What was discovered:
- Healing Gourd uses: 8
- Unused Gourd Seeds: 0
- Unused Prayer Beads: 2
- Prayer Necklaces found in inventory records: 6
- Derived Gourd Seeds found: 7 / 9
- Derived Prayer Beads found: 26 / 40
- Prayer Necklace count is included in the Prayer Bead derived total: `6 necklaces * 4 beads + 2 unused beads = 26`.

How it was verified:
- Scanned `USER_DATA000` for known item IDs listed in `data/sekiro/item-ids.json`.
- Prayer Bead ID `A00F0040` appears with quantity `2`.
- Gourd Seed ID `30110040` is absent as an unused inventory record.
- Healing Gourd ID `B80B0040` appears with quantity `8`.
- Parser tests assert `prayerNecklacesIncludedInDerivedTotal = true` in the Prayer Bead reconciliation report.

Evidence/source:
- `data/sekiro/item-ids.json`
- `research/reports/exact_location_report.json`

Confidence: Verified for this save

## Inventory record shape

What was discovered:
- Many inventory records in `USER_DATA000` have a mirror/prefix item ID immediately before the real item ID. Example pattern for item `xx yy zz 40`: `xx yy zz B0 xx yy zz 40 quantity`.
- This helps distinguish inventory quantities from incidental item ID references elsewhere in the slot.

How it was verified:
- Prayer Bead, Healing Gourd, and Prayer Necklace records in the provided save match this shape.
- The parser now prefers records with this mirror prefix when reading quantities.

Evidence/source:
- `packages/analyzer/src/sekiro/index.ts`
- Save analysis of `S0000.sl2` `USER_DATA000`

Confidence: Probable globally, Verified for the sampled records in this save
