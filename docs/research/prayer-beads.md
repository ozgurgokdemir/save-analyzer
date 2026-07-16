# Prayer Bead location mapping

## Status

All 40 primary Prayer Bead pickup, reward, and shop event flags decode with the verified record-1000 event-page layout. Their ON/OFF split matches the inventory-derived total in every sanitized fixture.

| Fixture | Primary flags ON | Primary flags OFF | Inventory-derived |
| --- | ---: | ---: | ---: |
| `001` | 26 | 14 | 26 / 40 |
| `002` | 28 | 12 | 28 / 40 |
| `003` | 33 | 7 | 33 / 40 |

The earlier reconciliation gap came from the discarded flat-offset decoder. Secondary ItemLotParam reward/replacement flags remain useful corroborating evidence, but the verified primary flags now determine the collected total directly.

## Fixture 001 missing locations

- Ashina Castle hidden chest
- Ashina Elite - Ujinari Mizou
- Fountainhead Palace underwater chest
- Headless Ape reward beads 1 and 2
- Hirata Audience Chamber hidden chest
- Juzou the Drunkard (Hirata revisit)
- Lone Shadow Masanaga (Hirata revisit)
- Lone Shadow Masanaga (Great Serpent Shrine)
- Mibu Village underwater chest
- Sakura Bull of the Palace
- Senpou Temple underwater
- Seven Ashina Spears - Shume Masaji Oniwa
- Shigekichi of the Red Guard

## Analysis rules

- A verified persistent primary flag ON means collected.
- The same flag OFF means missing.
- Inventory progression independently derives the total from unused beads and completed Prayer Necklaces.
- If primary flags do not reconcile with inventory evidence, unresolved exact locations are reported as `unknown` and the report includes a warning.
- Secondary ItemLotParam flags are retained as corroborating evidence and for future replacement-path research.

The canonical mappings and evidence live in `data/sekiro/prayer-beads.json`. Invalid save-specific byte annotations from the old decoder were removed.

## Remaining limits

Offering Box replacement behavior is still unmapped for saves where a missed bead later appears in the box. The three verified Sunken Valley pickup rows also need coordinate or EMEVD evidence to prove their exact ordering within that three-location group. This does not change the current fixtures because those three states agree.