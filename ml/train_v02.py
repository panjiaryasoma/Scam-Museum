#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
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


def models():
    lr = dict(
        class_weight="balanced",
        max_iter=4000,
        random_state=42,
        solver="liblinear",
    )

    return {
        "word_lr_v02": Pipeline([
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
        "char_lr_v02": Pipeline([
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
        "word_char_lr_v02": Pipeline([
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


def score_values(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    raw = model.decision_function(X)
    return 1.0 / (1.0 + np.exp(-raw))


def metrics(y, pred, score):
    return {
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
        "average_precision": float(average_precision_score(y, score)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def hmean(a, b):
    if a <= 0 or b <= 0:
        return 0.0
    return 2.0 * a * b / (a + b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--development", required=True, type=Path)
    ap.add_argument("--temporal-positive", required=True, type=Path)
    ap.add_argument("--primary-locked", required=True, type=Path)
    ap.add_argument("--reports-dir", default=Path("reports/v02"), type=Path)
    ap.add_argument("--models-dir", default=Path("models"), type=Path)
    args = ap.parse_args()

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    dev = pd.read_csv(args.development)
    temporal = pd.read_csv(args.temporal_positive)
    locked = pd.read_csv(args.primary_locked)

    required = {"text", "target", "template_group_id"}
    for name, df in [("development", dev), ("primary_locked", locked)]:
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{name} missing columns: {sorted(missing)}")

    if "text" not in temporal.columns:
        raise SystemExit("temporal-positive missing text column")

    X = dev["text"].fillna("").astype(str)
    y = dev["target"].astype(int)
    groups = dev["template_group_id"].astype(str)

    cv = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=2026,
    )

    candidates = models()
    rows = []
    summaries = {}

    for name, proto in candidates.items():
        fold_rows = []

        for fold, (tr, va) in enumerate(cv.split(X, y, groups)):
            tr_groups = set(groups.iloc[tr])
            va_groups = set(groups.iloc[va])
            assert not (tr_groups & va_groups)

            m = clone(proto)
            m.fit(X.iloc[tr], y.iloc[tr])
            pred = m.predict(X.iloc[va])
            score = score_values(m, X.iloc[va])
            result = metrics(y.iloc[va], pred, score)
            result.update({"model": name, "fold": fold})
            rows.append(result)
            fold_rows.append(result)

        cv_f1 = float(np.mean([r["f1_macro"] for r in fold_rows]))
        cv_precision = float(np.mean([r["precision_scam"] for r in fold_rows]))
        cv_recall = float(np.mean([r["recall_scam"] for r in fold_rows]))

        full = clone(proto)
        full.fit(X, y)

        temporal_text = temporal["text"].fillna("").astype(str)
        temporal_pred = full.predict(temporal_text)
        temporal_score = score_values(full, temporal_text)
        temporal_recall = float(np.mean(temporal_pred == 1))

        summaries[name] = {
            "cv_f1_macro_mean": cv_f1,
            "cv_precision_scam_mean": cv_precision,
            "cv_recall_scam_mean": cv_recall,
            "temporal_positive_recall": temporal_recall,
            "temporal_positive_n": int(len(temporal)),
            "selection_score": hmean(cv_f1, temporal_recall),
            "temporal_score_median": float(np.median(temporal_score)),
        }

    flat_rows = []
    for r in rows:
        copy = dict(r)
        copy.pop("confusion_matrix", None)
        flat_rows.append(copy)

    pd.DataFrame(flat_rows).to_csv(
        args.reports_dir / "v02_grouped_cv.csv",
        index=False,
    )

    eligible = {
        name: s for name, s in summaries.items()
        if s["cv_f1_macro_mean"] >= 0.95
    }
    if not eligible:
        raise RuntimeError(
            "No v0.2 model met minimum mean grouped-CV F1-macro >= 0.95"
        )

    selected = max(
        eligible,
        key=lambda n: (
            eligible[n]["selection_score"],
            eligible[n]["temporal_positive_recall"],
            eligible[n]["cv_f1_macro_mean"],
        ),
    )

    final_model = clone(candidates[selected])
    final_model.fit(X, y)

    locked_X = locked["text"].fillna("").astype(str)
    locked_y = locked["target"].astype(int)
    locked_pred = final_model.predict(locked_X)
    locked_score = score_values(final_model, locked_X)
    locked_metrics = metrics(
        locked_y,
        locked_pred,
        locked_score,
    )

    model_path = args.models_dir / "scam_classifier_v02.joblib"
    joblib.dump(final_model, model_path)

    report = {
        "selected_model": selected,
        "selection_rule": (
            "highest harmonic mean of grouped-CV F1-macro and "
            "IMC25 temporal positive recall, requiring CV F1-macro >= 0.95"
        ),
        "candidates": summaries,
        "primary_locked_test_after_selection": locked_metrics,
        "model_path": str(model_path),
    }

    (args.reports_dir / "v02_model_selection.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    md = [
        "# Scam Museum — v0.2 Model Selection",
        "",
        f"Selected model: **{selected}**",
        "",
        "| Model | CV F1-macro | Temporal recall | Selection score |",
        "|---|---:|---:|---:|",
    ]
    for name, s in sorted(summaries.items()):
        md.append(
            f"| {name} | "
            f"{s['cv_f1_macro_mean']:.4f} | "
            f"{s['temporal_positive_recall']:.4f} | "
            f"{s['selection_score']:.4f} |"
        )

    md += [
        "",
        "## Original primary locked test",
        "",
        f"- F1-macro: `{locked_metrics['f1_macro']:.4f}`",
        f"- Scam precision: `{locked_metrics['precision_scam']:.4f}`",
        f"- Scam recall: `{locked_metrics['recall_scam']:.4f}`",
        f"- Scam F1: `{locked_metrics['f1_scam']:.4f}`",
        f"- Average precision: `{locked_metrics['average_precision']:.4f}`",
        "",
        "This locked test was not used in model selection.",
    ]

    (args.reports_dir / "v02_model_selection.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
