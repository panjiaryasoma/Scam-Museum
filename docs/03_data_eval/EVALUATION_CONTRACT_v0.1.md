# SCAM MUSEUM — EVALUATION CONTRACT

**Version:** 0.1  
**Status:** Ready for Execution  
**Project:** Scam Museum  
**Primary Task:** English SMS smishing-risk classification  
**Date:** 29 August 2026

---

## 1. Purpose

Kontrak ini mengunci cara Scam Museum mengevaluasi model sebelum model dipakai oleh runtime.

Tujuannya bukan mengejar angka accuracy setinggi mungkin, tetapi memastikan bahwa:

- definisi label konsisten dengan produk;
- duplicate/template leakage diminimalkan;
- class imbalance tidak disembunyikan;
- model dibandingkan dengan baseline yang masuk akal;
- locked test tidak digunakan untuk tuning;
- external challenge tidak dicampur ke training;
- claim UI tidak lebih kuat daripada evidence.

---

## 2. Canonical Task

```yaml
task: binary_text_classification
language: English
input: raw SMS/message text
positive_class: SCAM_RISK
negative_class: LEGITIMATE
```

Canonical source mapping:

```yaml
ham:
  target: 0
  canonical: LEGITIMATE

smishing:
  target: 1
  canonical: SCAM_RISK

spam:
  target: null
  canonical: AMBIGUOUS_SPAM
  primary_training: excluded
```

Label matching wajib case-insensitive karena source file memiliki variasi capitalization.

---

## 3. Data Sources

### Primary

Mishra & Soni (2022), SMS Phishing Dataset for Machine Learning and Pattern Recognition.

Canonical source:

https://doi.org/10.17632/f45bkkt8pr.1

Expected original distribution:

```text
Ham       4,844
Spam        489
Smishing    638
Total     5,971
```

Primary binary pool sebelum cleaning:

```text
Ham + Smishing = 5,482 rows
```

### External Positive Challenge

Agarwal et al. (2025), IMC 2025 Smishing Dataset.

Repository:

https://github.com/reportsmishing/Smishing-Dataset-IMC25

Use:

```text
English rows
AND scam_type != spam
```

External data tidak boleh digunakan untuk model selection atau threshold tuning.

---

## 4. Audit Gate

Sebelum split dibuat, audit wajib mencatat:

- total rows;
- normalized label counts;
- missing text;
- empty text;
- exact duplicate messages;
- exact duplicates with conflicting labels;
- replacement-character / encoding artifacts;
- canonical-template group count;
- largest template groups;
- binary-class counts after exclusions;
- number of rows removed/quarantined.

### Conflict policy

Jika exact text yang sama memiliki conflicting canonical labels:

```text
LEGITIMATE vs SCAM_RISK
```

seluruh conflict group harus dikarantina dari primary benchmark.

Jangan memilih label mayoritas secara diam-diam.

### Same-label exact duplicates

Untuk primary benchmark:

```text
keep one representative row
```

agar repeated messages tidak memberi bobot berlebihan.

---

## 5. Template Grouping

Tujuan grouping adalah mencegah pesan yang nyaris sama tetapi hanya berbeda URL, nomor, atau nominal masuk ke train dan test sekaligus.

Template key dibuat dari text dengan transformasi untuk **grouping only**:

```text
Unicode normalize
lowercase
HTML unescape
replace email -> <EMAIL>
replace URL -> <URL>
replace phone-like tokens -> <PHONE>
replace currency/long numeric values -> <NUMBER>
collapse whitespace
```

Actual model input tetap mempertahankan raw message sebanyak mungkin.

---

## 6. Split Contract

### Stage A — Locked Test

Gunakan:

```text
StratifiedGroupKFold
n_splits = 5
shuffle = True
random_state = 42
```

Satu fold dipilih sebagai **locked test** (~20%).

Empat fold lain menjadi development set.

`group = template_group_id`

Tidak boleh ada group ID yang muncul di development dan locked test.

### Stage B — Development CV

Hanya development set yang digunakan untuk model selection.

Gunakan:

```text
StratifiedGroupKFold
n_splits = 5
shuffle = True
random_state = 1337
```

Semua preprocessing/vectorization harus berada di dalam sklearn Pipeline sehingga fit hanya terjadi pada training fold.

---

## 7. Model Candidates

### M0 — Dummy

```text
DummyClassifier(strategy="prior")
```

### M1 — Word LR

```text
TF-IDF word n-grams (1,2)
+
Logistic Regression
```

### M2 — Character LR

```text
TF-IDF char_wb n-grams (3,5)
+
Logistic Regression
```

### M3 — Word + Character LR

```text
FeatureUnion(
  word TF-IDF,
  char TF-IDF
)
+
Logistic Regression
```

Required initial setting:

```text
class_weight = balanced
max_iter >= 2000
random_state = 42
```

An unweighted LR variant boleh dibandingkan sebagai ablation.

No transformer is required for P0.

---

## 8. Primary Metric

Model selection metric:

```text
F1-macro
```

Reason:

- dataset imbalanced;
- both classes matter;
- accuracy dapat terlihat tinggi hanya dengan majority behavior.

---

## 9. Required Secondary Metrics

Pada CV dan locked test, laporkan:

```text
precision_scam
recall_scam
f1_scam
average_precision / PR-AUC
balanced_accuracy
confusion_matrix
```

Optional:

```text
ROC-AUC
Brier score
calibration curve
```

---

## 10. Selection Rule

Model final dipilih berdasarkan urutan:

1. highest mean grouped-CV F1-macro;
2. jika selisih <= 0.01, pilih model yang lebih sederhana;
3. jika masih seri, prioritaskan higher smishing recall tanpa precision collapse besar;
4. locked test hanya dijalankan setelah model dipilih.

Tidak boleh memilih ulang model karena model lain ternyata lebih bagus di locked test.

---

## 11. Probability / Risk-Band Contract

Probability tidak otomatis boleh disebut:

> “chance this message is a scam.”

Sebelum angka probability ditampilkan, minimal cek:

- Brier score;
- calibration behavior;
- reliability secara visual atau bin summary.

Jika calibration buruk:

```text
do not display percentage
```

Gunakan risk band:

```text
LOW RISK
SUSPICIOUS
HIGH RISK
```

Threshold risk band ditentukan hanya dari development OOF predictions.

Locked test tidak boleh dipakai untuk threshold tuning.

---

## 12. External IMC25 Challenge

Setelah model final dan threshold terkunci:

```text
filter language == English
exclude scam_type == spam
deduplicate exact/template overlap with primary data
```

Karena external set adalah positive-dominant challenge corpus, laporkan:

```text
external_smishing_recall
detected_count
missed_count
risk-band distribution
failure examples
```

Jangan laporkan accuracy atau specificity sebagai headline pada positive-only challenge set.

---

## 13. Ambiguous Spam Challenge

Source label `Spam` tidak menjadi ground truth scam atau legitimate.

Run separately setelah final model lock.

Laporkan:

```text
LOW / SUSPICIOUS / HIGH distribution
representative high-risk examples
representative low-risk examples
common triggers
```

Tujuan:

> mengetahui apakah classifier terlalu mudah menyamakan promosi/junk dengan fraud.

---

## 14. Acceptance Suite

Buat minimal 25 curated cases:

```text
5 obvious smishing
5 legitimate personal messages
5 legitimate service messages
5 promotional / ambiguous spam
5 obfuscated or adversarial scam messages
```

Acceptance checks:

- endpoint does not crash;
- no active malicious URL is opened;
- result schema valid;
- evidence spans remain inside input bounds;
- obvious credential/OTP requests surface evidence;
- benign urgency alone does not automatically force scam verdict.

Acceptance suite bukan pengganti statistical evaluation.

---

## 15. Evidence-Layer Evaluation Boundary

Deterministic evidence output harus disebut:

```text
Observed Evidence
```

bukan:

```text
Why the model predicted this
```

unless model explanation is actually computed.

Possible evidence taxonomy:

```text
TIME_URGENCY
AUTHORITY
NEED_AND_GREED
KINDNESS
HERD
DISTRACTION
DISHONESTY

OTP_REQUEST
CREDENTIAL_REQUEST
SUSPICIOUS_URL
PAYMENT_REQUEST
FINANCIAL_INFO_REQUEST
REPLY_OR_CALL_REQUEST
```

---

## 16. Reproducibility

Every benchmark report must record:

```text
dataset source/version
audit timestamp
input SHA256
cleaned dataset SHA256
split random seeds
grouping version
model configuration
sklearn version
Python version
```

Generated files:

```text
reports/primary_audit.json
reports/primary_audit.md
data/processed/primary_binary_clean.csv
data/processed/split_manifest.csv
reports/baseline_cv.csv
reports/model_selection.json
reports/locked_test.json
models/scam_classifier.joblib
models/model_metadata.json
```

---

## 17. Leakage Invariants

The evaluation pipeline must assert:

```text
development_group_ids ∩ test_group_ids == ∅
```

and for every CV fold:

```text
train_group_ids ∩ validation_group_ids == ∅
```

Vectorizers may not be fitted before split boundaries are applied.

No augmentation before split.

No external challenge data in training.

---

## 18. Stop Conditions

Do not ship model claims if any of these occur:

- label conflicts remain unresolved inside benchmark data;
- exact/template groups leak across locked boundaries;
- final model does not meaningfully beat Dummy baseline;
- locked-test smishing recall is unusably low;
- UI exposes probability despite obviously poor calibration;
- training cannot be reproduced from documented inputs.

The application may still be submitted as an experimental prototype if limitations are disclosed, but metrics must not be misrepresented.

---

## 19. Gate

| Requirement | Status |
|---|---|
| Label contract | LOCKED |
| Primary metric | LOCKED |
| Model candidate set | LOCKED |
| Group-aware split | LOCKED |
| Locked-test policy | LOCKED |
| External challenge role | LOCKED |
| Spam ambiguity policy | LOCKED |
| Audit executed | PENDING |
| Benchmark executed | PENDING |
| Final model selected | PENDING |
| Locked test executed | PENDING |

### Decision

**PASS TO DATA AUDIT + BASELINE BENCHMARK**

Production inference model remains blocked until model selection and locked-test evaluation are complete.
