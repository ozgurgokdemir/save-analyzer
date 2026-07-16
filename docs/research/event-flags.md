# Sekiro event flags

## Verified save layout

Sekiro 1.06 serializes event flags in record 1000 of each `USER_DATA###` slot entry. The parser reads record version 101 and treats the record payload at offset `0x34` as 128-byte flag pages.

An event ID is decoded with the bank base and world-block category tables in `data/sekiro/event-flag-layout.json`. Within that category, the thousands digit selects a page, the final three digits select a little-endian 32-bit word, and the flag uses MSB-first bit order in that word.

The complete address formula is maintained in the mapping file:

```text
record1000 + 0x34
+ (serializedBankBase + worldCategory) * 0x500
+ thousandsDigit * 0x80
+ floor((eventFlag % 1000) / 32) * 4
```

This replaces the earlier flat-offset hypothesis. Event IDs in unallocated banks or unmapped world blocks return `unknown` instead of reading unrelated bytes.

## Validation

The layout was verified read-only against Sekiro 1.06 runtime event pages and then checked against all three sanitized fixtures:

| Fixture | Gourd Seeds | Prayer Beads |
| --- | ---: | ---: |
| `001` | 7 / 9 | 26 / 40 |
| `002` | 8 / 9 | 28 / 40 |
| `003` | 8 / 9 | 33 / 40 |

For every fixture, primary location flags reconcile exactly with the independent inventory-derived totals.

The runtime investigation used process query/read permissions only. It did not write memory, inject code, suspend the process, or modify a save.

## Current consumers

The analyzer uses verified persistent event flags for:

- all nine Gourd Seed pickup and shop locations;
- all 40 Prayer Bead pickup, reward, and shop locations;
- 14 Memory-awarding major bosses;
- the three Ninjutsu Techniques;
- acquisition-backed Key Items.

SoulSplitter's published Sekiro mappings and the retained ItemLotParam and ShopLineupParam rows provide source and corroborating evidence. Primary persistent flags are authoritative for the exact collected/missing state in the current fixtures.

## Remaining limits

- Offering Box replacement behavior is not modeled as a general-purpose transfer mechanic.
- Three Sunken Valley Prayer Bead rows are verified as the correct group, but their exact row-to-location ordering still needs coordinate or EMEVD confirmation.
- Unknown is retained in the data model for unsupported event-ID banks, unmapped world blocks, corrupt saves, and future incomplete mappings.