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


def make_models():
    common = dict(class_weight="balanced", max_iter=4000, random_state=42, solver="liblinear")
    return {
        "word_lr_v03": Pipeline([
            ("tfidf", TfidfVectorizer(lowercase=True, strip_accents="unicode",
                                      ngram_range=(1, 2), min_df=2, max_df=0.995,
                                      sublinear_tf=True, max_features=120_000)),
            ("clf", LogisticRegression(**common)),
        ]),
        "char_lr_v03": Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", lowercase=True,
                                      ngram_range=(3, 5), min_df=2,
                                      sublinear_tf=True, max_features=180_000)),
            ("clf", LogisticRegression(**common)),
        ]),
        "word_char_lr_v03": Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(lowercase=True, strip_accents="unicode",
                                         ngram_range=(1, 2), min_df=2, max_df=0.995,
                                         sublinear_tf=True, max_features=100_000)),
                ("char", TfidfVectorizer(analyzer="char_wb", lowercase=True,
                                         ngram_range=(3, 5), min_df=2,
                                         sublinear_tf=True, max_features=160_000)),
            ])),
            ("clf", LogisticRegression(**common)),
        ]),
    }


def positive_score(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    raw = model.decision_function(X)
    return 1 / (1 + np.exp(-raw))


def metrics(y, pred, score):
    return {
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "precision_scam": float(precision_score(y, pred, pos_label=1, zero_division=0)),
        "recall_scam": float(recall_score(y, pred, pos_label=1, zero_division=0)),
        "f1_scam": float(f1_score(y, pred, pos_label=1, zero_division=0)),
        "average_precision": float(average_precision_score(y, score)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def hmean(a, b):
    return 0.0 if a <= 0 or b <= 0 else 2 * a * b / (a + b)


def normalize_primary(df):
    out = df.copy()
    out["text"] = out["text"].fillna("").astype(str).map(normalize_model_text)
    out["template_group_id"] = out["text"].map(canonical_template).map(short_hash)
    return out


def prepare_imc(df):
    out = df.copy()
    for col in ("text", "scam_type"):
        if col not in out.columns:
            raise SystemExit(f"IMC25 missing column: {col}")
    out["family"] = out["scam_type"].fillna("").astype(str).str.strip().str.casefold()
    out = out[(out["family"] != "") & (out["family"] != "spam")].copy()
    out["text"] = out["text"].fillna("").astype(str).map(normalize_model_text)
    out = out[out["text"].str.len() > 0].copy()
    out["template_group_id"] = out["text"].map(canonical_template).map(short_hash)
    out["target"] = 1

    family_counts = out.groupby("template_group_id")["family"].nunique()
    conflict_groups = set(family_counts[family_counts > 1].index.astype(str))
    clean = out[~out["template_group_id"].astype(str).isin(conflict_groups)].copy()
    return out, clean, conflict_groups


def cap_modern(df, held_out=None, max_per_template=5, max_per_family=2000):
    work = df.copy()
    if held_out is not None:
        work = work[work["family"] != held_out].copy()
    work = work.groupby("template_group_id", group_keys=False).head(max_per_template).copy()
    pieces = []
    for _, g in work.groupby("family"):
        if len(g) > max_per_family:
            g = g.sample(n=max_per_family, random_state=42)
        pieces.append(g)
    return pd.concat(pieces, ignore_index=True) if pieces else work.iloc[0:0].copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-manifest", required=True, type=Path)
    ap.add_argument("--imc25", required=True, type=Path)
    ap.add_argument("--reports-dir", default=Path("reports/v03"), type=Path)
    ap.add_argument("--models-dir", default=Path("models"), type=Path)
    ap.add_argument("--max-per-template", type=int, default=5)
    ap.add_argument("--max-per-family", type=int, default=2000)
    args = ap.parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    primary = normalize_primary(pd.read_csv(args.primary_manifest))
    primary_dev = primary[primary["split"].eq("development")].copy()
    primary_locked = primary[primary["split"].eq("locked_test")].copy()

    imc_all, imc_clean, conflicts = prepare_imc(pd.read_csv(args.imc25))
    families = sorted(imc_clean["family"].unique())
    models = make_models()

    # In-domain grouped CV on primary development only.
    Xp = primary_dev["text"].astype(str)
    yp = primary_dev["target"].astype(int)
    gp = primary_dev["template_group_id"].astype(str)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=2026)

    primary_cv = {}
    for name, proto in models.items():
        scores = []
        for tr, va in cv.split(Xp, yp, gp):
            assert not (set(gp.iloc[tr]) & set(gp.iloc[va]))
            m = clone(proto)
            m.fit(Xp.iloc[tr], yp.iloc[tr])
            scores.append(f1_score(yp.iloc[va], m.predict(Xp.iloc[va]), average="macro"))
        primary_cv[name] = {
            "f1_macro_mean": float(np.mean(scores)),
            "f1_macro_std": float(np.std(scores)),
        }

    model_reports = {}
    for name, proto in models.items():
        family_rows = []
        for held in families:
            modern_train = cap_modern(
                imc_clean, held_out=held,
                max_per_template=args.max_per_template,
                max_per_family=args.max_per_family,
            )
            test = imc_clean[imc_clean["family"].eq(held)].copy()

            train_groups = set(modern_train["template_group_id"].astype(str))
            test_groups = set(test["template_group_id"].astype(str))
            overlap = train_groups & test_groups
            if overlap:
                raise AssertionError(f"LOFO leakage for {held}: {len(overlap)}")

            train = pd.concat([
                primary_dev[["text", "target"]],
                modern_train[["text", "target"]],
            ], ignore_index=True)

            m = clone(proto)
            m.fit(train["text"].astype(str), train["target"].astype(int))
            pred = m.predict(test["text"].astype(str))
            recall = float(np.mean(pred == 1))

            family_rows.append({
                "family": held,
                "n": int(len(test)),
                "template_groups": int(test["template_group_id"].nunique()),
                "detected": int((pred == 1).sum()),
                "missed": int((pred == 0).sum()),
                "recall": recall,
                "group_overlap": int(len(overlap)),
            })

        macro = float(np.mean([r["recall"] for r in family_rows]))
        weighted = float(sum(r["recall"] * r["n"] for r in family_rows) / sum(r["n"] for r in family_rows))
        p_f1 = primary_cv[name]["f1_macro_mean"]
        model_reports[name] = {
            "primary_grouped_cv": primary_cv[name],
            "family_results": family_rows,
            "family_macro_recall": macro,
            "family_weighted_recall": weighted,
            "selection_score": hmean(p_f1, macro),
        }

    eligible = {
        k: v for k, v in model_reports.items()
        if v["primary_grouped_cv"]["f1_macro_mean"] >= 0.95
    }
    selected = max(
        eligible,
        key=lambda k: (
            eligible[k]["selection_score"],
            eligible[k]["family_macro_recall"],
            eligible[k]["primary_grouped_cv"]["f1_macro_mean"],
        ),
    )

    # Final v0.3 training uses all IMC families, capped.
    modern_final = cap_modern(
        imc_all,
        max_per_template=args.max_per_template,
        max_per_family=args.max_per_family,
    )

    # Protect original primary locked groups.
    locked_groups = set(primary_locked["template_group_id"].astype(str))
    modern_final = modern_final[
        ~modern_final["template_group_id"].astype(str).isin(locked_groups)
    ].copy()

    final_train = pd.concat([
        primary_dev[["text", "target"]],
        modern_final[["text", "target"]],
    ], ignore_index=True)

    final_model = clone(models[selected])
    final_model.fit(final_train["text"].astype(str), final_train["target"].astype(int))

    locked_y = primary_locked["target"].astype(int)
    locked_X = primary_locked["text"].astype(str)
    locked_pred = final_model.predict(locked_X)
    locked_result = metrics(locked_y, locked_pred, positive_score(final_model, locked_X))

    model_path = args.models_dir / "scam_classifier_v03.joblib"
    joblib.dump(final_model, model_path)

    report = {
        "version": "0.3",
        "imc_rows_nonspam": int(len(imc_all)),
        "imc_holdout_clean_rows": int(len(imc_clean)),
        "conflicting_template_groups_removed_from_lofo": int(len(conflicts)),
        "families": {f: int((imc_clean["family"] == f).sum()) for f in families},
        "selected_model": selected,
        "models": model_reports,
        "final_training_rows": int(len(final_train)),
        "final_training_class_counts": {
            str(k): int(v) for k, v in final_train["target"].value_counts().sort_index().items()
        },
        "primary_locked_test_after_selection": locked_result,
        "model_path": str(model_path),
    }

    out = args.reports_dir / "v03_family_generalization.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# Scam Museum — v0.3 Family Generalization",
        "",
        f"Selected model: **{selected}**",
        "",
        "| Model | Primary CV F1 | Family macro recall | Weighted recall | Selection score |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, r in model_reports.items():
        md.append(
            f"| {name} | {r['primary_grouped_cv']['f1_macro_mean']:.4f} | "
            f"{r['family_macro_recall']:.4f} | {r['family_weighted_recall']:.4f} | "
            f"{r['selection_score']:.4f} |"
        )
    md += ["", "## Selected model: held-out family recall", "",
           "| Family | n | Templates | Recall |", "|---|---:|---:|---:|"]
    for row in model_reports[selected]["family_results"]:
        md.append(f"| {row['family']} | {row['n']:,} | {row['template_groups']:,} | {row['recall']:.4f} |")
    md += [
        "",
        "## Original primary locked test",
        "",
        f"- F1-macro: `{locked_result['f1_macro']:.4f}`",
        f"- Scam precision: `{locked_result['precision_scam']:.4f}`",
        f"- Scam recall: `{locked_result['recall_scam']:.4f}`",
        f"- Scam F1: `{locked_result['f1_scam']:.4f}`",
    ]
    (args.reports_dir / "v03_family_generalization.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
