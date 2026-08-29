# SCAM MUSEUM — V0.4 HARD-NEGATIVE ROBUSTNESS PLAN

**Version:** 0.4  
**Status:** Ready to Run

## Why v0.4

v0.3 successfully improved unseen-family recall, but failed on the independent Financial Scams English benchmark:

```text
F1-macro          ≈ 0.496
Scam recall       ≈ 0.968
Balanced accuracy ≈ 0.553
```

The dominant failure was false positives on legitimate security/service messages.

The problem is therefore not insufficient scam recall.

The problem is:

> insufficient exposure to legitimate messages that look superficially scam-like.

## Development sources

### Primary 2022

Use original development split:

```text
LEGITIMATE + SCAM_RISK
```

Original locked test remains untouched until model/threshold selection ends.

### IMC25

Use modern English scam positives.

Cap repeated patterns:

```text
max 5 rows per normalized template
max 2000 rows per scam family
```

### Financial Scams 2025

The previous external benchmark is now explicitly converted into a development source.

Use:

```text
ENGLISH HAM ONLY
```

as hard negatives.

Do not add its scam rows to v0.4 training.

Reason:

The observed v0.3 failure is false-positive behavior, while positive coverage is already broad.

## Selection dimensions

Every candidate is evaluated on three independent development properties:

1. Primary grouped-CV F1-macro
2. Leave-one-scam-family-out macro recall on IMC25
3. Cross-validated hard-negative specificity on Financial English HAM

Thresholds are evaluated separately:

```text
0.50
0.60
0.70
0.80
0.90
```

Selection score:

```text
harmonic_mean(
    primary_grouped_cv_f1_macro,
    family_macro_recall,
    hard_negative_specificity
)
```

The architecture must maintain:

```text
primary grouped-CV F1-macro >= 0.95
```

## Final development training

After selecting model + threshold:

```text
Primary development
+
capped IMC25 positive
+
all Financial English hard-negative HAM
```

Then evaluate once on the original primary locked test.

## New final external benchmark

Use SmishX / SOUPS 2025.

Published dataset:

```text
1,200 SMS
622 legitimate
259 phishing
319 spam
```

Final Scam Museum benchmark maps:

```text
legitimate -> 0
phishing   -> 1
spam       -> excluded
```

Before evaluation:

- normalize;
- deduplicate;
- quarantine conflicting normalized groups;
- remove any normalized overlap with:
  - Primary dataset
  - IMC25
  - Financial hard-negative development set

No tuning after viewing the SmishX result.

## Final goal

v0.4 succeeds only if it keeps:

```text
strong scam-family generalization
+
materially lower hard-negative false positives
+
healthy original locked-test performance
+
healthy untouched SmishX cross-dataset metrics
```
