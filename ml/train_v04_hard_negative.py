#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ml.v02_text import canonical_template, normalize_model_text, short_hash

THRESHOLDS = [0.50, 0.60, 0.70, 0.80, 0.90]


def models():
    balanced = dict(
        class_weight="balanced",
        max_iter=5000,
        random_state=42,
        solver="liblinear",
    )
    plain = dict(
        class_weight=None,
        max_iter=5000,
        random_state=42,
        solver="liblinear",
    )

    def word(params):
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.995,
                sublinear_tf=True,
                max_features=140_000,
            )),
            ("clf", LogisticRegression(**params)),
        ])

    def char(params):
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                lowercase=True,
                ngram_range=(3, 5),
                min_df=2,
                sublinear_tf=True,
                max_features=200_000,
            )),
            ("clf", LogisticRegression(**params)),
        ])

    def word_char(params):
        return Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.995,
                    sublinear_tf=True,
                    max_features=110_000,
                )),
                ("char", TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                    max_features=180_000,
                )),
            ])),
            ("clf", LogisticRegression(**params)),
        ])

    return {
        "word_balanced_v04": word(balanced),
        "char_balanced_v04": char(balanced),
        "word_char_balanced_v04": word_char(balanced),
        "word_plain_v04": word(plain),
        "word_char_plain_v04": word_char(plain),
    }


def score(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    raw = model.decision_function(X)
    return 1 / (1 + np.exp(-raw))


def pred_at(scores, threshold):
    return (np.asarray(scores) >= threshold).astype(int)


def metric_bundle(y, pred, scores):
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
        "average_precision": float(average_precision_score(y, scores)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def harmonic(values):
    values = [float(v) for v in values]
    if any(v <= 0 for v in values):
        return 0.0
    return len(values) / sum(1 / v for v in values)


def normalize_primary(df):
    out = df.copy()
    out["text"] = out["text"].fillna("").astype(str).map(normalize_model_text)
    out["template_group_id"] = out["text"].map(canonical_template).map(short_hash)
    return out


def prepare_imc(df):
    out = df.copy()
    out["family"] = (
        out["scam_type"].fillna("").astype(str).str.strip().str.casefold()
    )
    out = out[
        (out["family"] != "")
        & (out["family"] != "spam")
    ].copy()
    out["text"] = out["text"].fillna("").astype(str).map(normalize_model_text)
    out = out[out["text"].str.len() > 0].copy()
    out["template_group_id"] = out["text"].map(canonical_template).map(short_hash)
    out["target"] = 1

    family_counts = out.groupby("template_group_id")["family"].nunique()
    conflicts = set(family_counts[family_counts > 1].index.astype(str))
    clean = out[
        ~out["template_group_id"].astype(str).isin(conflicts)
    ].copy()
    return out, clean, conflicts


def cap_modern(df, held_out=None, max_per_template=5, max_per_family=2000):
    work = df.copy()
    if held_out is not None:
        work = work[work["family"] != held_out].copy()

    work = (
        work.groupby("template_group_id", group_keys=False)
        .head(max_per_template)
        .copy()
    )

    pieces = []
    for _, group in work.groupby("family"):
        if len(group) > max_per_family:
            group = group.sample(n=max_per_family, random_state=42)
        pieces.append(group)

    return pd.concat(pieces, ignore_index=True) if pieces else work.iloc[0:0]


def prepare_hard_negative(df):
    if not {"text", "target"} <= set(df.columns):
        raise SystemExit("Financial prepared dataset requires text,target.")

    out = df[df["target"].astype(int).eq(0)].copy()
    out["text"] = out["text"].fillna("").astype(str).map(normalize_model_text)
    out["template_group_id"] = out["text"].map(canonical_template).map(short_hash)
    out = out.drop_duplicates("template_group_id").copy()
    out["target"] = 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-manifest", required=True, type=Path)
    ap.add_argument("--imc25", required=True, type=Path)
    ap.add_argument("--financial-prepared", required=True, type=Path)
    ap.add_argument("--reports-dir", default=Path("reports/v04"), type=Path)
    ap.add_argument("--models-dir", default=Path("models"), type=Path)
    ap.add_argument("--max-per-template", type=int, default=5)
    ap.add_argument("--max-per-family", type=int, default=2000)
    args = ap.parse_args()

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    primary = normalize_primary(pd.read_csv(args.primary_manifest))
    primary_dev = primary[primary["split"].eq("development")].copy()
    primary_locked = primary[primary["split"].eq("locked_test")].copy()

    imc_all, imc_clean, conflict_groups = prepare_imc(pd.read_csv(args.imc25))
    hardneg = prepare_hard_negative(pd.read_csv(args.financial_prepared))
    families = sorted(imc_clean["family"].unique())

    candidates = models()

    # A. Architecture sanity on original primary development.
    pX = primary_dev["text"].astype(str)
    py = primary_dev["target"].astype(int)
    pg = primary_dev["template_group_id"].astype(str)
    pcv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=2026)

    primary_cv = {}
    for name, proto in candidates.items():
        fold_scores = []
        for tr, va in pcv.split(pX, py, pg):
            m = clone(proto)
            m.fit(pX.iloc[tr], py.iloc[tr])
            pred = m.predict(pX.iloc[va])
            fold_scores.append(f1_score(py.iloc[va], pred, average="macro"))
        primary_cv[name] = {
            "f1_macro_mean": float(np.mean(fold_scores)),
            "f1_macro_std": float(np.std(fold_scores)),
        }

    # B. Hard-negative CV.
    # Every hard-negative fold is held out from model training.
    hX = hardneg["text"].astype(str)
    hg = hardneg["template_group_id"].astype(str)

    # deterministic 5-way assignment since every row is target=0
    rng = np.random.default_rng(2026)
    order = rng.permutation(len(hardneg))
    fold_ids = np.zeros(len(hardneg), dtype=int)
    for i, idx in enumerate(order):
        fold_ids[idx] = i % 5

    modern_full = cap_modern(
        imc_clean,
        max_per_template=args.max_per_template,
        max_per_family=args.max_per_family,
    )

    hardneg_results = {name: {t: [] for t in THRESHOLDS} for name in candidates}

    for fold in range(5):
        hn_train = hardneg[fold_ids != fold]
        hn_test = hardneg[fold_ids == fold]

        train = pd.concat([
            primary_dev[["text", "target"]],
            modern_full[["text", "target"]],
            hn_train[["text", "target"]],
        ], ignore_index=True)

        for name, proto in candidates.items():
            m = clone(proto)
            m.fit(train["text"].astype(str), train["target"].astype(int))
            scores = score(m, hn_test["text"].astype(str))

            for threshold in THRESHOLDS:
                pred = pred_at(scores, threshold)
                specificity = float(np.mean(pred == 0))
                hardneg_results[name][threshold].append(specificity)

    # C. Leave-one-family-out scores for every threshold.
    family_results = {
        name: {t: [] for t in THRESHOLDS}
        for name in candidates
    }

    for held in families:
        modern_train = cap_modern(
            imc_clean,
            held_out=held,
            max_per_template=args.max_per_template,
            max_per_family=args.max_per_family,
        )
        held_test = imc_clean[imc_clean["family"].eq(held)].copy()

        assert not (
            set(modern_train["template_group_id"].astype(str))
            & set(held_test["template_group_id"].astype(str))
        )

        train = pd.concat([
            primary_dev[["text", "target"]],
            modern_train[["text", "target"]],
            hardneg[["text", "target"]],
        ], ignore_index=True)

        for name, proto in candidates.items():
            m = clone(proto)
            m.fit(train["text"].astype(str), train["target"].astype(int))
            scores = score(m, held_test["text"].astype(str))

            for threshold in THRESHOLDS:
                pred = pred_at(scores, threshold)
                family_results[name][threshold].append({
                    "family": held,
                    "n": int(len(held_test)),
                    "template_groups": int(held_test["template_group_id"].nunique()),
                    "detected": int((pred == 1).sum()),
                    "missed": int((pred == 0).sum()),
                    "recall": float(np.mean(pred == 1)),
                })

    # D. Choose model + threshold.
    choices = []

    for name in candidates:
        primary_f1 = primary_cv[name]["f1_macro_mean"]
        if primary_f1 < 0.95:
            continue

        for threshold in THRESHOLDS:
            fam_rows = family_results[name][threshold]
            family_macro = float(np.mean([r["recall"] for r in fam_rows]))
            family_weighted = float(
                sum(r["recall"] * r["n"] for r in fam_rows)
                / sum(r["n"] for r in fam_rows)
            )
            hard_spec = float(
                np.mean(hardneg_results[name][threshold])
            )

            choices.append({
                "model": name,
                "threshold": threshold,
                "primary_cv_f1_macro": primary_f1,
                "family_macro_recall": family_macro,
                "family_weighted_recall": family_weighted,
                "hard_negative_specificity": hard_spec,
                "selection_score": harmonic([
                    primary_f1,
                    family_macro,
                    hard_spec,
                ]),
            })

    selected = max(
        choices,
        key=lambda r: (
            r["selection_score"],
            r["family_macro_recall"],
            r["hard_negative_specificity"],
        ),
    )

    selected_model_name = selected["model"]
    selected_threshold = float(selected["threshold"])

    # E. Final development train.
    final_train = pd.concat([
        primary_dev[["text", "target"]],
        modern_full[["text", "target"]],
        hardneg[["text", "target"]],
    ], ignore_index=True)

    final_model = clone(candidates[selected_model_name])
    final_model.fit(
        final_train["text"].astype(str),
        final_train["target"].astype(int),
    )

    # Evaluate original primary locked test only after selection.
    locked_X = primary_locked["text"].astype(str)
    locked_y = primary_locked["target"].astype(int)
    locked_scores = score(final_model, locked_X)
    locked_pred = pred_at(locked_scores, selected_threshold)
    locked_metrics = metric_bundle(
        locked_y,
        locked_pred,
        locked_scores,
    )

    model_path = args.models_dir / "scam_classifier_v04.joblib"
    metadata_path = args.models_dir / "scam_classifier_v04_metadata.json"

    joblib.dump(final_model, model_path)
    metadata = {
        "version": "0.4",
        "selected_model": selected_model_name,
        "threshold": selected_threshold,
        "selection": selected,
        "training_rows": int(len(final_train)),
        "training_class_counts": {
            str(k): int(v)
            for k, v in final_train["target"].value_counts().sort_index().items()
        },
        "hard_negative_rows": int(len(hardneg)),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = {
        "version": "0.4",
        "selected": selected,
        "all_choices": sorted(
            choices,
            key=lambda r: r["selection_score"],
            reverse=True,
        ),
        "primary_cv": primary_cv,
        "selected_family_results": family_results[
            selected_model_name
        ][selected_threshold],
        "selected_hard_negative_specificity_folds": hardneg_results[
            selected_model_name
        ][selected_threshold],
        "financial_hard_negative_rows": int(len(hardneg)),
        "imc_family_conflict_groups_removed": int(len(conflict_groups)),
        "final_training_rows": int(len(final_train)),
        "primary_locked_test_after_selection": locked_metrics,
        "model_path": str(model_path),
        "metadata_path": str(metadata_path),
    }

    (args.reports_dir / "v04_model_selection.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
