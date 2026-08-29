#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.v02_text import canonical_template, normalize_model_text, short_hash


def add_normalized_fields(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = df.copy()
    out["text_original"] = out["text"].fillna("").astype(str)
    out["text"] = out["text_original"].map(normalize_model_text)
    out = out[out["text"].str.len() > 0].copy()
    out["template"] = out["text"].map(canonical_template)
    out["template_group_id"] = out["template"].map(short_hash)
    out["source"] = source
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-manifest", required=True, type=Path)
    ap.add_argument("--imc25", required=True, type=Path)
    ap.add_argument(
        "--output-dir",
        default=Path("data/processed/v021"),
        type=Path,
    )
    ap.add_argument(
        "--temporal-quantile",
        type=float,
        default=0.75,
        help="Chronological cutoff quantile.",
    )
    ap.add_argument(
        "--max-train-per-template",
        type=int,
        default=20,
        help="Cap IMC25 historical rows per template group.",
    )
    args = ap.parse_args()

    if not 0.50 <= args.temporal_quantile <= 0.90:
        raise SystemExit("--temporal-quantile must be in [0.50, 0.90]")
    if args.max_train_per_template < 1:
        raise SystemExit("--max-train-per-template must be >= 1")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Primary corpus
    # -------------------------
    primary = pd.read_csv(args.primary_manifest)
    required_primary = {"text", "target", "split"}
    missing = required_primary - set(primary.columns)
    if missing:
        raise SystemExit(f"Primary manifest missing: {sorted(missing)}")

    primary = add_normalized_fields(primary, "primary_2022")

    primary_dev = primary[primary["split"].eq("development")].copy()
    primary_locked = primary[primary["split"].eq("locked_test")].copy()

    # -------------------------
    # IMC25 corpus
    # -------------------------
    imc = pd.read_csv(args.imc25)
    required_imc = {"text", "time"}
    missing = required_imc - set(imc.columns)
    if missing:
        raise SystemExit(f"IMC25 missing: {sorted(missing)}")

    imc = add_normalized_fields(imc, "imc25")
    imc["target"] = 1
    imc["date"] = pd.to_datetime(imc["time"], errors="coerce")
    imc = imc[imc["date"].notna()].copy()

    if imc.empty:
        raise SystemExit("No parseable IMC25 dates found.")

    # Date cutoff is row-based, but split membership is group-aware.
    cutoff = imc["date"].quantile(args.temporal_quantile)

    group_dates = (
        imc.groupby("template_group_id")["date"]
        .agg(first_seen="min", last_seen="max", rows="size")
        .reset_index()
    )

    # Historical group: the campaign/template ended on or before cutoff.
    historical_group_ids = set(
        group_dates.loc[
            group_dates["last_seen"] <= cutoff,
            "template_group_id",
        ].astype(str)
    )

    # Future group: has any occurrence after cutoff.
    # Groups crossing cutoff are withheld entirely from training.
    future_group_ids = set(
        group_dates.loc[
            group_dates["last_seen"] > cutoff,
            "template_group_id",
        ].astype(str)
    )

    overlap = historical_group_ids & future_group_ids
    if overlap:
        raise AssertionError(f"Historical/future group overlap: {len(overlap)}")

    # -------------------------
    # IMC historical training
    # -------------------------
    imc_hist = imc[
        imc["template_group_id"].astype(str).isin(historical_group_ids)
    ].copy()

    # Remove groups that collide with untouched primary locked test.
    locked_groups = set(primary_locked["template_group_id"].astype(str))
    hist_locked_overlap = (
        set(imc_hist["template_group_id"].astype(str)) & locked_groups
    )
    if hist_locked_overlap:
        imc_hist = imc_hist[
            ~imc_hist["template_group_id"].astype(str).isin(hist_locked_overlap)
        ].copy()

    # Retain multiple real messages per historical template, but cap
    # repeated campaigns so one campaign cannot dominate training.
    imc_hist = (
        imc_hist.sort_values("date")
        .groupby("template_group_id", group_keys=False)
        .tail(args.max_train_per_template)
        .copy()
    )

    # -------------------------
    # Temporal future challenge
    # -------------------------
    # IMPORTANT:
    # Keep ALL messages after the cutoff from future groups.
    # No one-row-per-template dedup here.
    imc_future = imc[
        (imc["date"] > cutoff)
        & imc["template_group_id"].astype(str).isin(future_group_ids)
    ].copy()

    # No future template may appear in historical training.
    train_imc_groups = set(imc_hist["template_group_id"].astype(str))
    eval_imc_groups = set(imc_future["template_group_id"].astype(str))
    temporal_group_overlap = train_imc_groups & eval_imc_groups
    if temporal_group_overlap:
        raise AssertionError(
            f"Temporal group leakage: {len(temporal_group_overlap)}"
        )

    # -------------------------
    # Build v0.2.1 development
    # -------------------------
    base_cols = ["text", "target", "template_group_id", "source"]

    optional_imc = [
        c for c in ["scam_type", "lure_principles", "date"]
        if c in imc.columns
    ]

    development = pd.concat(
        [
            primary_dev[base_cols],
            imc_hist[base_cols + optional_imc],
        ],
        ignore_index=True,
        sort=False,
    )

    # Primary locked test must remain untouched.
    dev_groups = set(development["template_group_id"].astype(str))
    locked_groups = set(primary_locked["template_group_id"].astype(str))
    primary_leak = dev_groups & locked_groups
    if primary_leak:
        raise AssertionError(
            f"Primary locked leakage into development: {len(primary_leak)}"
        )

    # -------------------------
    # Outputs
    # -------------------------
    dev_path = args.output_dir / "v021_development.csv"
    temporal_path = args.output_dir / "v021_imc25_temporal_positive.csv"
    locked_path = args.output_dir / "v021_primary_locked.csv"
    group_stats_path = args.output_dir / "v021_imc25_group_stats.csv"

    development.to_csv(dev_path, index=False)
    imc_future[base_cols + optional_imc].to_csv(temporal_path, index=False)
    primary_locked[base_cols].to_csv(locked_path, index=False)
    group_dates.to_csv(group_stats_path, index=False)

    summary = {
        "version": "0.2.1",
        "temporal_quantile": args.temporal_quantile,
        "cutoff": cutoff.isoformat(),
        "max_train_per_template": args.max_train_per_template,

        "primary_development_rows": int(len(primary_dev)),
        "primary_locked_rows": int(len(primary_locked)),

        "imc25_rows_with_valid_date": int(len(imc)),
        "imc25_exact_text_unique": int(imc["text_original"].nunique()),
        "imc25_template_groups_total": int(imc["template_group_id"].nunique()),

        "imc25_historical_groups": int(len(historical_group_ids)),
        "imc25_future_groups": int(len(future_group_ids)),

        "imc25_historical_training_rows_after_cap": int(len(imc_hist)),
        "imc25_future_temporal_rows": int(len(imc_future)),
        "imc25_future_temporal_groups": int(
            imc_future["template_group_id"].nunique()
        ),

        "imc25_rows_removed_due_primary_locked_group_overlap": int(
            len(hist_locked_overlap)
        ),

        "temporal_group_overlap": int(len(temporal_group_overlap)),
        "primary_locked_group_overlap": int(len(primary_leak)),

        "development_rows": int(len(development)),
        "development_class_counts": {
            str(k): int(v)
            for k, v in development["target"].value_counts().sort_index().items()
        },

        "outputs": {
            "development": str(dev_path),
            "temporal_positive": str(temporal_path),
            "primary_locked": str(locked_path),
            "imc25_group_stats": str(group_stats_path),
        },
    }

    summary_path = args.output_dir / "v021_corpus_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
