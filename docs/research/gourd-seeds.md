# Gourd Seed location mapping

## Status

All nine Gourd Seed locations have verified persistent pickup or shop event flags. With the record-1000 event-page decoder, the location states match the inventory-derived Gourd Seed totals in every sanitized fixture.

| Fixture | Collected | Missing | Missing locations |
| --- | ---: | ---: | --- |
| `001` | 7 | 2 | Mibu Village; Fountainhead Palace |
| `002` | 8 | 1 | Mibu Village |
| `003` | 8 | 1 | Mibu Village |

For fixture `001`, both merchant seeds - Battlefield Memorial Mob and Fujioka the Info Broker - are collected. The two missing seeds are the Mibu Village treasure and the Fountainhead Palace chest.

## Analysis rules

- A verified primary pickup or ShopLineupParam flag ON means the location is collected.
- The same persistent flag OFF means the location is missing.
- Inventory progression supplies an independent total: Healing Gourd uses plus unused Gourd Seeds.
- The category remains conservative if a flag cannot be addressed by the verified layout; that entity becomes `unknown` and reconciliation emits a warning.

The canonical row IDs, event flags, locations, and source evidence live in `data/sekiro/gourd-seeds.json`. Save-specific byte-offset annotations from the discarded flat-offset decoder were removed because they were not valid evidence.

## Verification

Regression tests assert both summary counts and exact missing location IDs for fixture `001`, and repeat exact-location reconciliation for fixtures `002` and `003`.