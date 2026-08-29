#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline


def make_models():
    common_lr = dict(
        class_weight="balanced",
        max_iter=3000,
        random_state=42,
        solver="liblinear",
    )

    return {
        "dummy_prior": Pipeline([
            ("tfidf", TfidfVectorizer(min_df=2)),
            ("clf", DummyClassifier(strategy="prior")),
        ]),
        "word_lr": Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.995,
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(**common_lr)),
        ]),
        "char_lr": Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                lowercase=True,
                ngram_range=(3, 5),
                min_df=2,
                max_features=120_000,
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(**common_lr)),
        ]),
        "word_char_lr": Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.995,
                    sublinear_tf=True,
                    max_features=80_000,
                )),
                ("char", TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                    max_features=120_000,
                )),
            ])),
            ("clf", LogisticRegression(**common_lr)),
        ]),
    }


def positive_score(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        raw = model.decision_function(X)
        return 1 / (1 + np.exp(-raw))
    return model.predict(X).astype(float)


def metrics(y_true, y_pred, score):
    return {
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "precision_scam": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_scam": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_scam": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "average_precision": float(average_precision_score(y_true, score)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--reports-dir", default=Path("reports"), type=Path)
    ap.add_argument("--models-dir", default=Path("models"), type=Path)
    args = ap.parse_args()

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.manifest)
    dev = df[df["split"] == "development"].reset_index(drop=True)
    test = df[df["split"] == "locked_test"].reset_index(drop=True)

    X = dev["text"].astype(str)
    y = dev["target"].astype(int)
    groups = dev["template_group_id"].astype(str)

    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=1337)
    models = make_models()
    rows = []

    for name, prototype in models.items():
        for fold, (tr, va) in enumerate(cv.split(X, y, groups)):
            tr_groups = set(groups.iloc[tr])
            va_groups = set(groups.iloc[va])
            assert not (tr_groups & va_groups)

            model = clone(prototype)
            model.fit(X.iloc[tr], y.iloc[tr])
            pred = model.predict(X.iloc[va])
            score = positive_score(model, X.iloc[va])
            result = metrics(y.iloc[va], pred, score)
            result.update({"model": name, "fold": fold})
            rows.append(result)

    cv_df = pd.DataFrame(rows)
    flat = cv_df.drop(columns=["confusion_matrix"])
    flat.to_csv(args.reports_dir / "baseline_cv.csv", index=False)

    summary = (
        flat.groupby("model")
        .agg({
            "f1_macro": ["mean", "std"],
            "precision_scam": ["mean", "std"],
            "recall_scam": ["mean", "std"],
            "f1_scam": ["mean", "std"],
            "average_precision": ["mean", "std"],
            "balanced_accuracy": ["mean", "std"],
        })
    )
    print(summary)

    means = flat.groupby("model")["f1_macro"].mean().sort_values(ascending=False)
    best_name = means.index[0]

    # Simplicity tie rule: within 0.01 of best, prefer word_lr, then char_lr, then word_char_lr.
    best_score = means.iloc[0]
    eligible = set(means[means >= best_score - 0.01].index)
    preference = ["word_lr", "char_lr", "word_char_lr", "dummy_prior"]
    selected = next((m for m in preference if m in eligible), best_name)

    final_model = clone(models[selected])
    final_model.fit(dev["text"].astype(str), dev["target"].astype(int))

    test_pred = final_model.predict(test["text"].astype(str))
    test_score = positive_score(final_model, test["text"].astype(str))
    locked = metrics(test["target"].astype(int), test_pred, test_score)
    locked["model"] = selected
    locked["n_test"] = int(len(test))
    locked["class_counts"] = {
        str(k): int(v) for k, v in test["target"].value_counts().sort_index().items()
    }

    joblib.dump(final_model, args.models_dir / "scam_classifier.joblib")
    (args.reports_dir / "locked_test.json").write_text(
        json.dumps(locked, indent=2), encoding="utf-8"
    )

    selection = {
        "selected_model": selected,
        "selection_metric": "mean grouped-CV F1-macro",
        "cv_mean_f1_macro": {k: float(v) for k, v in means.items()},
        "tie_tolerance": 0.01,
        "locked_test": locked,
    }
    (args.reports_dir / "model_selection.json").write_text(
        json.dumps(selection, indent=2), encoding="utf-8"
    )

    print("\nSelected:", selected)
    print(json.dumps(locked, indent=2))


if __name__ == "__main__":
    main()
