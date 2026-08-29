# Scam Museum v0.3 — Quick Run

Copy `ml/train_v03_family_holdout.py` into the repository. It reuses the existing `ml/v02_text.py`.

Run:

```powershell
uv run python ml/train_v03_family_holdout.py `
  --primary-manifest data/processed/split_manifest.csv `
  --imc25 data/processed/imc25_english_challenge.csv
```

Outputs:

```text
models/scam_classifier_v03.joblib

reports/v03/
├── v03_family_generalization.json
└── v03_family_generalization.md
```

Inspect especially:

- `family_macro_recall`
- `wrong number` recall
- `hey mum/dad` recall
- original primary locked-test F1-macro

After v0.3 is frozen, use Financial Scams Detection Dataset v2 only as the final untouched external benchmark.
