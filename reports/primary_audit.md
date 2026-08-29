# Scam Museum — Primary Dataset Audit

- Raw rows: **5,971**
- Encoding used: `utf-8`
- Missing text rows: **0**
- Empty normalized text rows: **0**
- Rows containing replacement character `�`: **145**
- Exact duplicate groups (all labels): **133**
- Conflicting exact groups (binary labels): **0**
- Same-label exact duplicate rows removed from binary pool: **86**
- Final binary rows: **5,396**
- Unique template groups: **5,303**

## Normalized Source Labels

- `ham`: 4,844
- `smishing`: 638
- `spam`: 489

## Final Binary Classes

- `LEGITIMATE`: 4,834
- `SCAM_RISK`: 562

## Notes

- `Spam` is intentionally excluded from primary binary training.
- Exact label conflicts are quarantined rather than majority-voted.
- Canonical templates are used for group-aware splitting, not as runtime model input.
