# Sekiro Save Fixtures

Committed fixtures use this structure:

```text
sekiro/<fixture-id>/S0000.sl2
```

Fixture IDs are immutable, zero-padded identifiers allocated sequentially. They are not version numbers.

Every committed `S0000.sl2` is privacy-sanitized and covered by the fixture privacy test. Unsanitized player saves must never be committed.