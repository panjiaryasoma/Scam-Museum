# Scam Museum v0.5 — Quick Run

Copy `ml/train_v05_multisource.py` into the repository. It reuses the existing `ml/v02_text.py`.

Run:

```powershell
uv run python ml/train_v05_multisource.py `
  --primary-manifest data/processed/split_manifest.csv `
  --imc25 data/processed/imc25_english_challenge.csv `
  --financial-prepared data/processed/final_external_financial_english.csv `
  --smishx-raw data/raw/smishx_dataset.csv
```

Outputs:

```text
models/scam_classifier_v05.joblib
models/scam_classifier_v05_metadata.json
reports/v05/v05_model_selection.json
```

Inspect especially:

```text
selected.model
selected.threshold
selected.primary_oof_f1_macro
selected.family_macro_recall
selected.family_min_recall
selected.negative_source_macro_specificity
selected.negative_source_min_specificity
primary_locked_test_after_selection
```

Do not touch the next untouched external benchmark until v0.5 selection is complete.
