#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def get_positive_scores(model, texts):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(texts)[:, 1]
    if hasattr(model, "decision_function"):
        raw = model.decision_function(texts)
        return 1.0 / (1.0 + np.exp(-raw))
    return model.predict(texts).astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, type=Path)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--reports-dir", default=Path("reports"), type=Path)
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    args.reports_dir.mkdir(parents=True, exist_ok=True)

    model = joblib.load(args.model)
    df = pd.read_csv(args.input)

    if "text" not in df.columns:
        raise SystemExit("Expected column 'text' in external challenge CSV.")

    texts = df["text"].fillna("").astype(str)
    scores = get_positive_scores(model, texts)
    pred = (scores >= args.threshold).astype(int)

    df = df.copy()
    df["scam_score"] = scores
    df["predicted_scam"] = pred

    n = len(df)
    detected = int(pred.sum())
    missed = int((pred == 0).sum())
    recall = detected / n if n else 0.0

    summary = {
        "dataset": str(args.input),
        "model": str(args.model),
        "threshold": args.threshold,
        "n_external_positive": n,
        "detected_count": detected,
        "missed_count": missed,
        "external_smishing_recall": recall,
        "score_summary": {
            "min": float(np.min(scores)) if n else None,
            "p05": float(np.quantile(scores, 0.05)) if n else None,
            "median": float(np.median(scores)) if n else None,
            "p95": float(np.quantile(scores, 0.95)) if n else None,
            "max": float(np.max(scores)) if n else None,
        },
    }

    if "scam_type" in df.columns:
        by_type = []
        for scam_type, group in df.groupby("scam_type", dropna=False):
            g_pred = group["predicted_scam"].to_numpy()
            total = len(group)
            hit = int(g_pred.sum())
            by_type.append({
                "scam_type": None if pd.isna(scam_type) else str(scam_type),
                "n": total,
                "detected": hit,
                "missed": total - hit,
                "recall": hit / total if total else None,
            })
        summary["by_scam_type"] = sorted(
            by_type,
            key=lambda x: (x["recall"] if x["recall"] is not None else -1, -x["n"])
        )

    if "lure_principles" in df.columns:
        lure_rows = []
        exploded = (
            df.assign(
                _lure=df["lure_principles"]
                .fillna("")
                .astype(str)
                .str.split(",")
            )
            .explode("_lure")
        )
        exploded["_lure"] = exploded["_lure"].str.strip()
        exploded = exploded[exploded["_lure"] != ""]

        for lure, group in exploded.groupby("_lure"):
            total = len(group)
            hit = int(group["predicted_scam"].sum())
            lure_rows.append({
                "lure": str(lure),
                "n": total,
                "detected": hit,
                "missed": total - hit,
                "recall": hit / total if total else None,
            })

        summary["by_lure"] = sorted(
            lure_rows,
            key=lambda x: (x["recall"] if x["recall"] is not None else -1, -x["n"])
        )

    out_json = args.reports_dir / "imc25_external_challenge.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    scored_path = args.reports_dir / "imc25_external_scored.csv"
    df.to_csv(scored_path, index=False)

    missed_df = df[df["predicted_scam"] == 0].copy()
    missed_df = missed_df.sort_values("scam_score", ascending=True)
    missed_path = args.reports_dir / "imc25_missed_cases.csv"
    missed_df.to_csv(missed_path, index=False)

    md = [
        "# Scam Museum — IMC25 External Challenge",
        "",
        f"- External positive rows: **{n:,}**",
        f"- Detected: **{detected:,}**",
        f"- Missed: **{missed:,}**",
        f"- External smishing recall: **{recall:.4f}**",
        f"- Threshold: `{args.threshold}`",
        "",
        "## Score summary",
        "",
    ]

    for k, v in summary["score_summary"].items():
        if v is not None:
            md.append(f"- {k}: `{v:.4f}`")

    if "by_scam_type" in summary:
        md += ["", "## Recall by scam type", "", "| Scam type | n | Recall |", "|---|---:|---:|"]
        for row in summary["by_scam_type"]:
            name = row["scam_type"] if row["scam_type"] is not None else "(missing)"
            md.append(f"| {name} | {row['n']:,} | {row['recall']:.4f} |")

    if "by_lure" in summary:
        md += ["", "## Recall by lure", "", "| Lure | n | Recall |", "|---|---:|---:|"]
        for row in summary["by_lure"]:
            md.append(f"| {row['lure']} | {row['n']:,} | {row['recall']:.4f} |")

    (args.reports_dir / "imc25_external_challenge.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print("\nWrote:")
    print(out_json)
    print(scored_path)
    print(missed_path)
    print(args.reports_dir / "imc25_external_challenge.md")


if __name__ == "__main__":
    main()
