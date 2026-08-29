# SCAM MUSEUM — DATASET & LABEL STRATEGY

**Version:** 0.1  
**Status:** Proposed Lock  
**Project:** Scam Museum  
**Hackathon:** HackSocial 2026  
**Language Scope:** English-first  
**Date:** 29 August 2026

---

## 1. Decision Summary

Scam Museum v1 akan menggunakan **dua lapisan dataset**:

1. **Primary training/evaluation dataset**  
   Mishra & Soni (2022), *SMS PHISHING DATASET FOR MACHINE LEARNING AND PATTERN RECOGNITION*.

2. **External positive challenge dataset**  
   Agarwal et al. (2025), *Fishing for Smishing: Understanding SMS Phishing Infrastructure and Strategies by Mining Public User Reports*.

Primary model tetap mengerjakan **binary smishing-risk classification**.

```text
SMISHING   -> positive class
HAM        -> negative class
SPAM       -> excluded from primary training target
```

`SPAM` tidak digabung otomatis ke `SCAM`, karena unsolicited commercial/junk messages tidak identik dengan phishing atau fraud.

---

# 2. Primary Dataset

## Mishra & Soni SMS Phishing Dataset

**Source:** Mendeley Data  
**DOI:** https://doi.org/10.17632/f45bkkt8pr.1  
**Published:** 20 June 2022  
**License:** CC BY 4.0  
**Language:** English SMS  
**Total rows:** 5,971

Original labels:

| Source label | Count | Meaning |
|---|---:|---|
| `Ham` | 4,844 | legitimate SMS |
| `Spam` | 489 | unsolicited/junk SMS |
| `Smishing` | 638 | SMS phishing / malicious social engineering |

Available fields include:

```text
LABEL
TEXT
URL
EMAIL
PHONE
```

For Scam Museum P0, the model will use **TEXT only**.

Derived `URL`, `EMAIL`, and `PHONE` fields will not be fed directly into the primary classifier because similar signals are handled separately by the deterministic evidence layer.

### Why this is the primary dataset

Advantages:

- already contains `Ham`, `Spam`, and `Smishing` as separate concepts;
- directly matches short-message / SMS domain;
- English;
- raw message text is available;
- small enough for rapid local experiments;
- CC BY 4.0;
- suitable for TF-IDF + linear classifier benchmarking.

Limitations:

- dataset is imbalanced;
- smishing class is relatively small;
- collection sources may create source-specific artifacts;
- source messages are older than the current scam ecosystem;
- exact/near duplicates must be audited before splitting.

---

# 3. External Challenge Dataset

## IMC 2025 Smishing Dataset

**Source:** reportsmishing / ACM IMC 2025  
**Repository:** https://github.com/reportsmishing/Smishing-Dataset-IMC25  
**Paper DOI:** https://doi.org/10.1145/3730567.3764431  
**License:** CC BY 4.0

The research corpus contains updated public smishing reports from multiple online forums.

The paper reports:

- 33,869 analyzed smishing text messages;
- 66 detected languages;
- 22,078 English messages (~65%);
- scam-category labels;
- lure-principle labels;
- impersonated-brand annotations;
- PII-sanitized message text.

Relevant fields include:

```text
Text Message
Translated Text Message
Scam Category
Lure Principles
Language
Brand Impersonated
URL Shortener
```

### Use in Scam Museum

This dataset will **not** be mixed blindly into the primary train/test split.

For v1 it is an **external positive challenge set**:

```text
language == English
AND
scam_category != Spam
```

After deduplication against the primary dataset, this set tests whether the trained classifier still detects newer real-world smishing patterns.

Because this challenge set is positive-only, report:

```text
external_smishing_recall
detected_count
missed_count
failure examples
```

Do **not** report:

```text
accuracy
F1
specificity
```

on this external set because it does not provide a representative negative class.

---

# 4. Why UCI SMS Spam Is Not the Main Dataset

The UCI SMS Spam Collection is high-quality, CC BY 4.0, and contains 5,574 English SMS messages.

However its labels are:

```text
HAM
SPAM
```

not:

```text
LEGITIMATE
SCAM
```

Spam includes unsolicited advertising and other unwanted messages that are not necessarily fraudulent.

Therefore:

> `SPAM != SCAM`

Additionally, the Mishra & Soni dataset references earlier SMS spam resources including work by Almeida et al., so merging UCI data without an overlap audit could introduce duplicate leakage.

UCI may be used only as a fallback or supplementary source after overlap analysis.

---

# 5. Primary Label Contract

## Model target

```yaml
task: binary_text_classification

labels:
  0: LEGITIMATE
  1: SCAM_RISK
```

Source mapping:

```yaml
Ham:
  model_label: 0
  canonical_label: LEGITIMATE

Smishing:
  model_label: 1
  canonical_label: SCAM_RISK

Spam:
  model_label: null
  canonical_label: AMBIGUOUS_SPAM
  training_use: excluded
```

### Why `Spam` is excluded

A spam message may be:

- annoying;
- unsolicited;
- promotional;
- manipulative;

without necessarily attempting credential theft, financial fraud, impersonation, or phishing.

Mapping all spam messages to `SCAM_RISK` would silently change the product task from:

> smishing / scam-risk detection

into:

> unwanted-message detection.

That is not the product we designed.

---

# 6. User-Facing Labels

Internal model output:

```text
LEGITIMATE
SCAM_RISK
```

User-facing output remains:

```text
LOW RISK
SUSPICIOUS
HIGH RISK
```

Exact thresholds are **not yet locked**.

Thresholds must be selected using training-side cross-validation / out-of-fold predictions and must never be tuned against the locked test set.

The UI should not display:

```text
"92% chance this is a scam"
```

unless probability calibration is explicitly evaluated.

Safer default:

```text
HIGH RISK

This message contains textual patterns commonly associated
with smishing and several independently detected risk signals.
```

---

# 7. Evidence Taxonomy

Scam Museum separates two kinds of evidence.

## 7.1 Manipulation Lures

The initial taxonomy follows the seven lure principles used in the IMC 2025 smishing study:

```text
TIME_URGENCY
AUTHORITY
NEED_AND_GREED
KINDNESS
HERD
DISTRACTION
DISHONESTY
```

These are manipulation strategies.

Examples:

```text
"Act within 10 minutes"
-> TIME_URGENCY

"Official Revenue Service notice"
-> AUTHORITY

"You have won $3,000"
-> NEED_AND_GREED
```

## 7.2 Operational Risk Indicators

These are observable message characteristics, not psychological lures:

```text
CREDENTIAL_REQUEST
OTP_REQUEST
SUSPICIOUS_URL
PAYMENT_REQUEST
FINANCIAL_INFO_REQUEST
REPLY_OR_CALL_REQUEST
```

Example:

```text
"Enter the OTP sent to your phone"
-> OTP_REQUEST
-> CREDENTIAL_REQUEST
```

### Important boundary

```text
Manipulation lure != operational risk indicator
```

and:

```text
Detected evidence != causal explanation of the ML model
```

The UI must keep these concepts separate.

---

# 8. Exhibit Title Mapping

The museum layer may turn the dominant evidence into a title.

Examples:

| Dominant signal | Exhibit title |
|---|---|
| `TIME_URGENCY` | **The Urgency Trap** |
| `AUTHORITY` | **Portrait of a Fake Authority** |
| `NEED_AND_GREED` | **Still Life with Free Money** |
| `KINDNESS` | **The Kindness Hook** |
| `HERD` | **Everyone Else Already Clicked** |
| `DISTRACTION` | **Study in Distraction** |
| `DISHONESTY` | **Invitation to Complicity** |
| no dominant lure | **Untitled (Suspicious Message)** |

Titles are presentation logic, not ML labels.

---

# 9. Data Cleaning Contract

Before any train/test split:

1. preserve raw text;
2. remove empty rows;
3. normalize label spelling;
4. calculate exact duplicate hashes;
5. build a canonical template representation;
6. assign a `group_id`;
7. inspect label conflicts within duplicate/template groups.

Canonical template normalization may:

```text
lowercase
normalize whitespace
replace URLs with <URL>
replace emails with <EMAIL>
replace phone-like sequences with <PHONE>
replace long numeric codes with <NUMBER>
```

Do not aggressively remove punctuation or scam obfuscation from the actual model input.

The canonical form is primarily for **grouping/deduplication**, not necessarily for inference.

---

# 10. Leakage Prevention

A major risk is template leakage.

Example:

```text
Your account expires in 24 hours. Visit <URL>.
Your account expires in 48 hours. Visit <URL>.
```

A random row split may place nearly identical templates in both train and test.

Therefore the preferred split is **group-aware**.

Proposed approach:

```text
canonicalized message
        ↓
template/group ID
        ↓
StratifiedGroupKFold
```

No synthetic augmentation, oversampling, or resampling is allowed before split creation.

---

# 11. Split Strategy

Primary dataset after filtering:

```text
Ham + Smishing
```

Recommended evaluation design:

### Locked test

Use one group-stratified fold as an untouched final test set.

Approximate target:

```text
80% development
20% locked test
```

### Model selection

On the development partition:

```text
5-fold StratifiedGroupKFold
```

Use cross-validation for:

- model comparison;
- hyperparameter selection;
- risk-threshold exploration.

The locked test is evaluated only after model selection.

---

# 12. Model Candidates

Keep the benchmark deliberately small.

## Baseline 0

```text
DummyClassifier
```

Purpose:

- sanity check;
- proves the model beats trivial class-frequency behavior.

## Baseline 1

```text
word TF-IDF
+
Logistic Regression
```

## Candidate 2

```text
character TF-IDF
+
Logistic Regression
```

Useful for:

- obfuscated words;
- URLs;
- spelling variation;
- scam formatting;
- short-text morphology.

## Candidate 3

```text
word TF-IDF
+
character TF-IDF
+
Logistic Regression
```

Likely final candidate if it provides meaningful lift.

No transformer model is required for P0.

---

# 13. Class Imbalance Policy

Primary training counts are naturally imbalanced.

Do not synthesize thousands of smishing messages merely to make the class chart look prettier.

Initial policy:

```python
LogisticRegression(class_weight="balanced")
```

Compare against unweighted baseline.

If class weighting harms precision excessively, report it and choose based on evaluation.

Synthetic augmentation is **out of scope for P0**.

---

# 14. Evaluation Metrics

## Primary metric

```text
F1-macro
```

Reason:

Both legitimate and smishing performance matter, while the dataset is imbalanced.

## Required secondary metrics

```text
Smishing precision
Smishing recall
Smishing F1
PR-AUC
Confusion matrix
```

Optional:

```text
ROC-AUC
Brier score / calibration diagnostic
```

Accuracy alone is insufficient.

---

# 15. External Evaluation

## IMC25 Challenge

After the final model is locked:

1. filter IMC25 to English messages;
2. remove `Spam`;
3. remove exact/near overlap with primary data;
4. run inference;
5. report recall and failure analysis.

This is a **temporal/domain challenge**, not a second test set with equivalent semantics.

Example reporting:

```text
Primary locked test:
F1-macro = TBD
Smishing recall = TBD
PR-AUC = TBD

IMC25 external positive challenge:
Recall = TBD
Missed cases = TBD
```

Do not blend both numbers into one headline metric.

---

# 16. Ambiguous Spam Evaluation

The 489 `Spam` rows from the primary source should be preserved separately.

Purpose:

> inspect how often the scam classifier interprets non-phishing spam as high risk.

This is a challenge set, not standard ground truth.

Report:

```text
LOW / SUSPICIOUS / HIGH distribution
common false-alarm patterns
qualitative examples
```

Do not claim that predicting `LOW` or `HIGH` is always objectively correct for these rows.

---

# 17. Curated Acceptance Cases

In addition to statistical evaluation, create a small manually reviewed suite.

Minimum:

```text
5 obvious smishing
5 legitimate personal messages
5 legitimate service-style messages
5 ambiguous promotional/spam messages
5 adversarial/obfuscated scam messages
```

Total:

```text
25 acceptance cases
```

Curated examples must be:

- synthetic;
- sanitized; or
- safely derived from licensed sources.

No real OTP, credentials, personal phone number, or active malicious URL.

---

# 18. Dataset Provenance in Repository

Recommended structure:

```text
data/
├── README.md
├── raw/
│   └── .gitkeep
├── processed/
│   └── .gitkeep
└── samples/
    └── acceptance_cases.csv

docs/03_data_eval/
├── DATASET_LABEL_STRATEGY.md
├── EVALUATION_CONTRACT.md
└── THIRD_PARTY_DATA_NOTICE.md
```

Do not commit external datasets blindly.

At minimum document:

```text
dataset name
authors
DOI / source URL
license
download date
original labels
transformations performed
```

If a modified CC BY dataset is redistributed, attribution and modification notes must be preserved.

---

# 19. Claims Allowed After This Strategy

Before benchmark:

> Scam Museum is designed to screen English suspicious messages using a lightweight text classifier and a separate evidence layer.

After successful primary evaluation:

> The classifier was evaluated on a held-out, group-separated portion of the Mishra & Soni SMS phishing dataset.

After successful external challenge:

> The locked model was additionally challenged against newer English smishing samples from the IMC 2025 corpus.

Do not claim:

```text
real-world fraud prevention rate
universal phishing detection
production-grade threat intelligence
multilingual support
validated probability of fraud
```

---

# 20. Known Risks

## Source artifacts

A classifier may learn differences between collection sources rather than scam semantics.

Mitigation:

- template grouping;
- external challenge set;
- failure analysis.

## Temporal drift

2022 scam language may differ from 2025–2026 campaigns.

Mitigation:

- IMC25 external positive challenge.

## Spam / scam confusion

Promotional spam can contain urgency, rewards, and URLs.

Mitigation:

- keep `Spam` outside binary ground truth;
- inspect it separately.

## Class imbalance

Smishing is much smaller than Ham.

Mitigation:

- macro metrics;
- class weighting;
- PR-AUC;
- no accuracy-only reporting.

## Explanation mismatch

Rule evidence is not automatically a model explanation.

Mitigation:

- label UI sections separately:
  - `ML Risk Screening`
  - `Observed Evidence`

---

# 21. Dataset Gate

| Gate | Status |
|---|---|
| Primary dataset identified | PASS |
| Primary dataset license clear | PASS — CC BY 4.0 |
| Target domain matches short messages | PASS |
| Positive label semantically defined | PASS |
| Negative label semantically defined | PASS |
| Spam ambiguity handled explicitly | PASS |
| External challenge source identified | PASS |
| English-first boundary defined | PASS |
| Leakage strategy defined | PASS |
| Final dataset audit executed | PENDING |
| Duplicate statistics known | PENDING |
| Final class counts after cleaning known | PENDING |
| Benchmark executed | PENDING |

## Gate Decision

**PASS TO DATA AUDIT & EVALUATION IMPLEMENTATION**

The label contract is sufficiently defined to begin downloading, auditing, splitting, and benchmarking the primary dataset.

Production model selection remains blocked until the dataset audit and evaluation results exist.
