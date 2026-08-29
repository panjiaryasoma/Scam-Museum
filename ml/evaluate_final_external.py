#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def positive_score(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    raw = model.decision_function(X)
    return 1 / (1 + np.exp(-raw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, type=Path)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument(
        "--output",
        default=Path("reports/v02/final_external_benchmark.json"),
        type=Path,
    )
    args = ap.parse_args()

    model = joblib.load(args.model)
    df = pd.read_csv(args.input)

    required = {"text", "target"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing: {sorted(missing)}")

    X = df["text"].fillna("").astype(str)
    y = df["target"].astype(int)

    pred = model.predict(X)
    score = positive_score(model, X)

    result = {
        "n": int(len(df)),
        "class_counts": {
            str(k): int(v)
            for k, v in y.value_counts().sort_index().items()
        },
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "precision_scam": float(
            precision_score(y, pred, pos_label=1, zero_division=0)
        ),
        "recall_scam": float(
            recall_score(y, pred, pos_label=1, zero_division=0)
        ),
        "f1_scam": float(
            f1_score(y, pred, pos_label=1, zero_division=0)
        ),
        "average_precision": float(
            average_precision_score(y, score)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y, pred)
        ),
        "confusion_matrix": confusion_matrix(
            y, pred, labels=[0, 1]
        ).tolist(),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    scored = df.copy()
    scored["score"] = score
    scored["prediction"] = pred
    scored.to_csv(
        args.output.with_suffix(".scored.csv"),
        index=False,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
