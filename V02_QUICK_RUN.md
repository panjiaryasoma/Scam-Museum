# Scam Museum v0.2 — Quick Run

## A. Build v0.2 development corpus

```powershell
uv run python scripts/build_v02_corpus.py `
  --primary-manifest data/processed/split_manifest.csv `
  --imc25 data/processed/imc25_english_challenge.csv
```

Expected:

```text
data/processed/v02/v02_development.csv
data/processed/v02/v02_imc25_temporal_positive.csv
data/processed/v02/v02_primary_locked.csv
data/processed/v02/v02_corpus_summary.json
```

## B. Train v0.2 candidates

```powershell
uv run python ml/train_v02.py `
  --development data/processed/v02/v02_development.csv `
  --temporal-positive data/processed/v02/v02_imc25_temporal_positive.csv `
  --primary-locked data/processed/v02/v02_primary_locked.csv
```

Expected:

```text
models/scam_classifier_v02.joblib
reports/v02/v02_grouped_cv.csv
reports/v02/v02_model_selection.json
reports/v02/v02_model_selection.md
```

Do not overwrite `scam_classifier.joblib` from v0.1 yet.

---

# C. Download NEW final external benchmark

Financial Scams Detection Dataset v2:

https://doi.org/10.17632/znsk27yk3h.2

Place its CSV in:

```text
data/raw/financial_scams_v2.csv
```

The source contains English and Bangla real scam/ham messages. The preparation script will attempt to autodetect columns.

First try:

```powershell
uv run python scripts/prepare_final_external.py `
  --input data/raw/financial_scams_v2.csv `
  --exclude data/processed/v02/v02_development.csv `
  --exclude data/processed/v02/v02_primary_locked.csv `
  --exclude data/processed/v02/v02_imc25_temporal_positive.csv
```

If column autodetection fails, the script prints all source columns. Then rerun with:

```powershell
uv run python scripts/prepare_final_external.py `
  --input data/raw/financial_scams_v2.csv `
  --text-col YOUR_TEXT_COLUMN `
  --label-col YOUR_LABEL_COLUMN `
  --language-col YOUR_LANGUAGE_COLUMN `
  --exclude data/processed/v02/v02_development.csv `
  --exclude data/processed/v02/v02_primary_locked.csv `
  --exclude data/processed/v02/v02_imc25_temporal_positive.csv
```

---

# D. Final external benchmark

Only after v0.2 model selection is complete:

```powershell
uv run python ml/evaluate_final_external.py `
  --model models/scam_classifier_v02.joblib `
  --input data/processed/final_external_financial_english.csv
```

After this command, treat the final external dataset as read-only evaluation evidence.

Do not tune v0.2 based on its result.
