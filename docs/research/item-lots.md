# Sekiro ItemLotParam and ShopLineupParam evidence

ItemLotParam and ShopLineupParam rows connect world rewards and merchant inventory to persistent event flags. The canonical mappings are stored with each category under `data/sekiro`.

## Current use

- Gourd Seeds use nine verified pickup or shop flags.
- Prayer Beads use 40 verified primary pickup, reward, or shop flags.
- Secondary Prayer Bead ItemLotParam flags are retained as corroborating reward/replacement evidence.
- Prosthetic tools and upgrades retain their acquisition or inventory evidence.
- Memory-awarding major bosses use their verified progression flags.
- Ninjutsu Techniques use acquisition flags 6745-6747.
- Acquisition-backed Key Items use verified persistent flags.

Primary Gourd Seed and Prayer Bead flags now reconcile directly with inventory totals across fixtures `001`, `002`, and `003`. The older secondary-evidence reconciliation gap was an artifact of the discarded event decoder.

## Status semantics

For a verified persistent primary flag:

- ON means the mapped location or reward is collected.
- OFF means it is missing.
- An unsupported bank, unmapped block, or unreadable record yields `unknown`.

Inventory-derived totals remain an independent consistency check. If location evidence and inventory progression disagree, the analyzer warns and avoids claiming unsupported exact attribution.

## Sources and maintenance

Mapping evidence comes from Sekiro parameter tables, SoulSplitter's published flag lists, community location guides, read-only runtime verification, and cross-fixture reconciliation. Save-specific offsets from the old flat-offset model are not retained as evidence.

Tests cover the row/event mappings, category totals, exact missing-location sets, and privacy of every numeric fixture directory discovered under `research/fixtures/sekiro`.