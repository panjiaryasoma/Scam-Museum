# SCAM MUSEUM — V0.2 ROBUST RETRAINING PLAN

**Version:** 0.2  
**Status:** Experimental / Ready to Run  
**Goal:** Improve cross-domain generalization without falsifying evaluation claims.

---

## 1. Why v0.2 Exists

v0.1 produced:

```text
Primary grouped locked test:
F1-macro ≈ 0.9807
Smishing recall = 1.0000

IMC25 external positive challenge:
Recall ≈ 0.7143
```

This indicates meaningful domain shift.

Failure categories included conversational and socially contextual scam families such as:

```text
wrong number
hey mum/dad
kindness-based lures
dishonesty-based lures
```

The v0.1 model should therefore be understood as a strong classic-smishing classifier, not a universal scam detector.

---

## 2. Methodological Reset

Because IMC25 results have already been inspected, IMC25 can no longer remain the untouched final external benchmark if it is used for retraining.

For v0.2:

```text
PRIMARY 2022
Mishra & Soni
    +
IMC25 EARLIER DATA
modern positive examples
    ↓
V0.2 DEVELOPMENT / TRAINING

IMC25 LATER DATA
    ↓
TEMPORAL DEVELOPMENT CHALLENGE

Mishra original locked test
    ↓
IN-DOMAIN HOLDOUT CHECK

Financial Scams Detection Dataset v2 (2025)
    ↓
NEW FINAL EXTERNAL BENCHMARK
```

The Financial Scams dataset must not be used for training, model selection, or threshold tuning.

---

## 3. V0.2 Training Goal

Improve generalization to:

- conversational scams;
- impersonation;
- family/emergency scams;
- wrong-number scams;
- delivery scams;
- government scams;
- banking scams;
- scams without obvious classic phishing vocabulary.

No synthetic training data is required.

---

## 4. Feature Strategy

Candidates:

```text
WORD TF-IDF + Logistic Regression
CHAR TF-IDF + Logistic Regression
WORD + CHAR TF-IDF + Logistic Regression
```

v0.2 intentionally remains lightweight.

Reason:

Data coverage is currently a larger limitation than model capacity.

A transformer may be explored later, but it is not allowed to replace proper external evaluation.

---

## 5. Cross-Source Normalization

Primary and IMC25 data use different collection conventions.

Before training, normalize source-specific artifacts:

```text
real URLs / <URL> placeholders     -> <URL>
phone numbers / <PHONE_NUMBER>     -> <PHONE>
email addresses                    -> <EMAIL>
dates / <DATE_TIME>                -> <DATE>
named-entity placeholders          -> <ENTITY>
location placeholders              -> <LOCATION>
long numeric identifiers           -> <NUMBER>
```

This reduces the risk that the classifier learns dataset provenance rather than scam semantics.

Normalization is deterministic and applied identically to every corpus.

---

## 6. IMC25 Temporal Split

IMC25 is split by time, not randomly.

Rules:

1. normalize and group near-template messages;
2. calculate each template group's date range;
3. use an approximate 75% chronological cutoff;
4. groups entirely before the cutoff may enter development training;
5. any group crossing the cutoff is held out from training;
6. groups after/crossing the cutoff form the temporal positive challenge.

Use one representative per IMC25 template group in training to reduce repeated-campaign dominance.

---

## 7. Original Primary Holdout

The original Mishra locked test remains untouched.

v0.2 training uses only rows originally assigned to:

```text
split == development
```

The original:

```text
split == locked_test
```

is never added to training.

This preserves an in-domain comparison point.

---

## 8. Model Selection

Development CV:

```text
StratifiedGroupKFold
5 folds
```

For every candidate collect:

```text
CV F1-macro
CV scam precision
CV scam recall
CV PR-AUC
temporal IMC25 recall
```

Selection score:

```text
harmonic_mean(
    CV F1-macro,
    temporal IMC25 recall
)
```

A model must maintain:

```text
mean CV F1-macro >= 0.95
```

to qualify.

This prevents selecting a model that obtains high future-positive recall simply by predicting everything as scam.

The original locked test is evaluated only after selection.

---

## 9. Final External Benchmark

Candidate:

**Financial Scams Detection Dataset v2 (2025)**

Use only the English subset.

Expected semantic labels:

```text
scam -> 1
ham  -> 0
```

Before evaluation:

- normalize text;
- deduplicate;
- quarantine conflicting exact duplicates;
- remove exact overlap with all training/development corpora;
- preserve class counts.

Report:

```text
F1-macro
scam precision
scam recall
scam F1
PR-AUC
balanced accuracy
confusion matrix
```

No tuning after viewing this final benchmark.

---

## 10. Future-Pattern Claim

v0.2 is not allowed to claim:

> “predicts future scams.”

Allowed framing:

> “The model is trained on a broader range of historical scam patterns and evaluated using temporal and cross-dataset tests to measure robustness to previously unseen scam styles.”

Future runtime may introduce:

```text
UNKNOWN / UNFAMILIAR PATTERN
```

for uncertain messages.

That is an abstention mechanism, not fortune-telling.

---

## 11. Gate

v0.2 is considered an improvement only if:

```text
[ ] CV F1-macro remains >= 0.95
[ ] temporal IMC25 recall materially improves
[ ] original locked-test performance remains healthy
[ ] new external Financial Scams benchmark is acceptable
[ ] no external benchmark is used for tuning
```

If final external performance is still weak, keep v0.1/v0.2 claims narrow and ship the evidence layer rather than manufacturing confidence.
