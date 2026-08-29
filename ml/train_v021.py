#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
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
    lr = dict(
        class_weight="balanced",
        max_iter=4000,
        random_state=42,
        solver="liblinear",
    )

    return {
        "word_lr_v021": Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.995,
                sublinear_tf=True,
                max_features=120_000,
            )),
            ("clf", LogisticRegression(**lr)),
        ]),
        "char_lr_v021": Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                lowercase=True,
                ngram_range=(3, 5),
                min_df=2,
                sublinear_tf=True,
                max_features=180_000,
            )),
            ("clf", LogisticRegression(**lr)),
        ]),
        "word_char_lr_v021": Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.995,
                    sublinear_tf=True,
                    max_features=100_000,
                )),
                ("char", TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                    max_features=160_000,
                )),
            ])),
            ("clf", LogisticRegression(**lr)),
        ]),
    }


def positive_score(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    raw = model.decision_function(X)
    return 1 / (1 + np.exp(-raw))


def metrics(y_true, pred, score):
    return {
        "f1_macro": float(f1_score(y_true, pred, average="macro")),
        "precision_scam": float(
            precision_score(y_true, pred, pos_label=1, zero_division=0)
        ),
        "recall_scam": float(
            recall_score(y_true, pred, pos_label=1, zero_division=0)
        ),
        "f1_scam": float(
            f1_score(y_true, pred, pos_label=1, zero_division=0)
        ),
        "average_precision": float(
            average_precision_score(y_true, score)
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_true, pred)
        ),
        "confusion_matrix": confusion_matrix(
            y_true, pred, labels=[0, 1]
        ).tolist(),
    }


def hmean(a, b):
    if a <= 0 or b <= 0:
        return 0.0
    return 2 * a * b / (a + b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--development", required=True, type=Path)
    ap.add_argument("--temporal-positive", required=True, type=Path)
    ap.add_argument("--primary-locked", required=True, type=Path)
    ap.add_argument(
        "--reports-dir",
        default=Path("reports/v021"),
        type=Path,
    )
    ap.add_argument(
        "--models-dir",
        default=Path("models"),
        type=Path,
    )
    args = ap.parse_args()

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    dev = pd.read_csv(args.development)
    temporal = pd.read_csv(args.temporal_positive)
    locked = pd.read_csv(args.primary_locked)

    required = {"text", "target", "template_group_id"}
    for label, df in [("development", dev), ("primary_locked", locked)]:
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{label} missing: {sorted(missing)}")

    if "text" not in temporal.columns:
        raise SystemExit("temporal-positive missing text")

    X = dev["text"].fillna("").astype(str)
    y = dev["target"].astype(int)
    groups = dev["template_group_id"].astype(str)

    temporal_X = temporal["text"].fillna("").astype(str)

    cv = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=2026,
    )

    candidates = make_models()
    fold_rows = []
    summary = {}

    for name, proto in candidates.items():
        model_fold_results = []

        for fold, (tr, va) in enumerate(cv.split(X, y, groups)):
            assert not (
                set(groups.iloc[tr]) & set(groups.iloc[va])
            )

            model = clone(proto)
            model.fit(X.iloc[tr], y.iloc[tr])

            pred = model.predict(X.iloc[va])
            score = positive_score(model, X.iloc[va])

            result = metrics(y.iloc[va], pred, score)
            result.update({"model": name, "fold": fold})
            model_fold_results.append(result)
            fold_rows.append(result)

        cv_f1 = float(np.mean([
            r["f1_macro"] for r in model_fold_results
        ]))
        cv_precision = float(np.mean([
            r["precision_scam"] for r in model_fold_results
        ]))
        cv_recall = float(np.mean([
            r["recall_scam"] for r in model_fold_results
        ]))

        full_model = clone(proto)
        full_model.fit(X, y)

        temporal_pred = full_model.predict(temporal_X)
        temporal_score = positive_score(full_model, temporal_X)
        temporal_recall = float(np.mean(temporal_pred == 1))

        summary[name] = {
            "cv_f1_macro_mean": cv_f1,
            "cv_precision_scam_mean": cv_precision,
            "cv_recall_scam_mean": cv_recall,
            "temporal_positive_recall": temporal_recall,
            "temporal_positive_n": int(len(temporal)),
            "temporal_template_groups": int(
                temporal["template_group_id"].nunique()
            ) if "template_group_id" in temporal.columns else None,
            "selection_score": hmean(cv_f1, temporal_recall),
            "temporal_score_median": float(
                np.median(temporal_score)
            ),
        }

    flat_rows = []
    for row in fold_rows:
        item = dict(row)
        item.pop("confusion_matrix", None)
        flat_rows.append(item)

    pd.DataFrame(flat_rows).to_csv(
        args.reports_dir / "v021_grouped_cv.csv",
        index=False,
    )

    eligible = {
        name: values
        for name, values in summary.items()
        if values["cv_f1_macro_mean"] >= 0.95
    }
    if not eligible:
        raise RuntimeError(
            "No v0.2.1 candidate met grouped-CV F1-macro >= 0.95"
        )

    selected = max(
        eligible,
        key=lambda name: (
            eligible[name]["selection_score"],
            eligible[name]["temporal_positive_recall"],
            eligible[name]["cv_f1_macro_mean"],
        ),
    )

    final_model = clone(candidates[selected])
    final_model.fit(X, y)

    locked_X = locked["text"].fillna("").astype(str)
    locked_y = locked["target"].astype(int)

    locked_pred = final_model.predict(locked_X)
    locked_score = positive_score(final_model, locked_X)
    locked_result = metrics(
        locked_y,
        locked_pred,
        locked_score,
    )

    model_path = args.models_dir / "scam_classifier_v021.joblib"
    joblib.dump(final_model, model_path)

    report = {
        "version": "0.2.1",
        "selected_model": selected,
        "selection_rule": (
            "Highest harmonic mean of grouped-CV F1-macro "
            "and group-disjoint temporal IMC25 recall, "
            "requiring grouped-CV F1-macro >= 0.95."
        ),
        "development_rows": int(len(dev)),
        "development_class_counts": {
            str(k): int(v)
            for k, v in y.value_counts().sort_index().items()
        },
        "temporal_rows": int(len(temporal)),
        "temporal_template_groups": int(
            temporal["template_group_id"].nunique()
        ) if "template_group_id" in temporal.columns else None,
        "candidates": summary,
        "primary_locked_test_after_selection": locked_result,
        "model_path": str(model_path),
    }

    (args.reports_dir / "v021_model_selection.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
