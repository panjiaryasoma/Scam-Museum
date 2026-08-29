# Scam Museum — Data Audit Quick Run

## 1. Download canonical primary dataset

Source of truth:

https://doi.org/10.17632/f45bkkt8pr.1

Download `Dataset_5971.zip`, extract the CSV, and place it at:

```text
data/raw/Dataset_5971.csv
```

Do not treat random Kaggle/GitHub mirrors as the citation source even if a mirror is used temporarily for convenience.

## 2. Download IMC25 external challenge

Repository:

https://github.com/reportsmishing/Smishing-Dataset-IMC25

Copy:

```text
dataset/final_dataset_output.csv
```

to:

```text
data/raw/imc25_final_dataset_output.csv
```

## 3. Create environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -r requirements-eval.txt
```

## 4. Audit primary dataset

```bash
python scripts/audit_primary_dataset.py ^
  --input data/raw/Dataset_5971.csv
```

PowerShell one-line:

```powershell
python scripts/audit_primary_dataset.py --input data/raw/Dataset_5971.csv
```

Outputs:

```text
data/processed/primary_binary_clean.csv
data/processed/ambiguous_spam.csv
reports/primary_audit.json
reports/primary_audit.md
```

## 5. Build leakage-controlled split

```powershell
python scripts/build_splits.py --input data/processed/primary_binary_clean.csv
```

Output:

```text
data/processed/split_manifest.csv
```

## 6. Benchmark

```powershell
python ml/train_baselines.py --manifest data/processed/split_manifest.csv
```

Outputs:

```text
reports/baseline_cv.csv
reports/model_selection.json
reports/locked_test.json
models/scam_classifier.joblib
```

## 7. Prepare external challenge

```powershell
python scripts/prepare_imc25_challenge.py --input data/raw/imc25_final_dataset_output.csv --primary-clean data/processed/primary_binary_clean.csv
```

No external challenge data is used for training.
