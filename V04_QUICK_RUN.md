# Scam Museum v0.4 — Quick Run

## Files required from earlier work

```text
ml/v02_text.py
data/processed/split_manifest.csv
data/processed/imc25_english_challenge.csv
data/processed/final_external_financial_english.csv
```

The Financial dataset is no longer an external test in v0.4. Its HAM rows are used as development hard negatives.

## 1. Train/select v0.4

```powershell
uv run python ml/train_v04_hard_negative.py `
  --primary-manifest data/processed/split_manifest.csv `
  --imc25 data/processed/imc25_english_challenge.csv `
  --financial-prepared data/processed/final_external_financial_english.csv
```

Outputs:

```text
models/scam_classifier_v04.joblib
models/scam_classifier_v04_metadata.json
reports/v04/v04_model_selection.json
```

Inspect:

```text
selected.model
selected.threshold
selected.family_macro_recall
selected.hard_negative_specificity
primary_locked_test_after_selection
```

## 2. Obtain SmishX dataset

Use the official `data/dataset.csv` from:

`yizhu-joy/SmishX`

Save it as:

```text
data/raw/smishx_dataset.csv
```

Do not inspect model performance on it yet.

## 3. Prepare final SmishX benchmark

```powershell
uv run python scripts/prepare_smishx_final.py `
  --input data/raw/smishx_dataset.csv `
  --exclude data/processed/split_manifest.csv `
  --exclude data/processed/imc25_english_challenge.csv `
  --exclude data/processed/final_external_financial_english.csv
```

The script excludes SmishX `spam` and evaluates only:

```text
legitimate -> 0
phishing   -> 1
```

## 4. Final external evaluation

Run ONCE after v0.4 model and threshold are frozen:

```powershell
uv run python ml/evaluate_smishx_final.py `
  --model models/scam_classifier_v04.joblib `
  --metadata models/scam_classifier_v04_metadata.json `
  --input data/processed/smishx_final_external.csv
```

Do not tune after viewing this result.
