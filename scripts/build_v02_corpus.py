#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Allow importing sibling ml module when script is run from repo root.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.v02_text import canonical_template, normalize_model_text, short_hash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary-manifest", required=True, type=Path)
    ap.add_argument("--imc25", required=True, type=Path)
    ap.add_argument("--output-dir", default=Path("data/processed/v02"), type=Path)
    ap.add_argument("--temporal-quantile", type=float, default=0.75)
    args = ap.parse_args()

    if not 0.5 <= args.temporal_quantile <= 0.9:
        raise SystemExit("--temporal-quantile must be between 0.5 and 0.9")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    primary = pd.read_csv(args.primary_manifest)
    required_primary = {"text", "target", "template_group_id", "split"}
    missing = required_primary - set(primary.columns)
    if missing:
        raise SystemExit(f"Primary manifest missing: {sorted(missing)}")

    # Keep original split boundary.
    primary_dev = primary[primary["split"].eq("development")].copy()
    primary_locked = primary[primary["split"].eq("locked_test")].copy()

    for frame in (primary_dev, primary_locked):
        frame["text_original"] = frame["text"].fillna("").astype(str)
        frame["text"] = frame["text_original"].map(normalize_model_text)
        frame["template"] = frame["text"].map(canonical_template)
        frame["template_group_id"] = frame["template"].map(short_hash)
        frame["source"] = "primary_2022"

    imc = pd.read_csv(args.imc25)
    required_imc = {"text"}
    missing = required_imc - set(imc.columns)
    if missing:
        raise SystemExit(f"IMC25 file missing: {sorted(missing)}")

    imc["text_original"] = imc["text"].fillna("").astype(str)
    imc["text"] = imc["text_original"].map(normalize_model_text)
    imc = imc[imc["text"].str.len() > 0].copy()
    imc["template"] = imc["text"].map(canonical_template)
    imc["template_group_id"] = imc["template"].map(short_hash)
    imc["target"] = 1
    imc["source"] = "imc25"

    if "time" not in imc.columns:
        raise SystemExit(
            "IMC25 file must contain 'time' for temporal v0.2 split."
        )

    imc["date"] = pd.to_datetime(imc["time"], errors="coerce")
    dated = imc[imc["date"].notna()].copy()
    if dated.empty:
        raise SystemExit("No parseable IMC25 dates found.")

    # Group-level dates prevent campaign/template leakage across temporal cutoff.
    group_dates = (
        dated.groupby("template_group_id")["date"]
        .agg(["min", "max"])
        .reset_index()
    )

    cutoff = dated["date"].quantile(args.temporal_quantile)

    early_group_ids = set(
        group_dates.loc[group_dates["max"] <= cutoff, "template_group_id"]
    )
    temporal_group_ids = set(
        group_dates.loc[group_dates["max"] > cutoff, "template_group_id"]
    )

    if early_group_ids & temporal_group_ids:
        raise AssertionError("Temporal group leakage")

    imc_early = dated[dated["template_group_id"].isin(early_group_ids)].copy()
    imc_temporal = dated[dated["template_group_id"].isin(temporal_group_ids)].copy()

    # One representative per campaign/template group.
    imc_early = (
        imc_early.sort_values("date")
        .drop_duplicates("template_group_id", keep="last")
        .copy()
    )
    imc_temporal = (
        imc_temporal.sort_values("date")
        .drop_duplicates("template_group_id", keep="last")
        .copy()
    )

    # Prevent exact/template overlap with primary locked test.
    locked_groups = set(primary_locked["template_group_id"].astype(str))
    overlap_locked = set(imc_early["template_group_id"].astype(str)) & locked_groups
    if overlap_locked:
        imc_early = imc_early[
            ~imc_early["template_group_id"].astype(str).isin(overlap_locked)
        ].copy()

    keep = [
        "text",
        "target",
        "template_group_id",
        "source",
    ]
    optional = ["scam_type", "lure_principles", "date"]

    dev = pd.concat(
        [
            primary_dev[keep],
            imc_early[[c for c in keep + optional if c in imc_early.columns]],
        ],
        ignore_index=True,
        sort=False,
    )

    # Defensive check: no template group from original locked set in development.
    dev_groups = set(dev["template_group_id"].astype(str))
    primary_locked_groups = set(primary_locked["template_group_id"].astype(str))
    primary_leak = dev_groups & primary_locked_groups
    if primary_leak:
        raise AssertionError(
            f"Primary locked group leakage into v0.2 development: {len(primary_leak)}"
        )

    dev_path = args.output_dir / "v02_development.csv"
    temporal_path = args.output_dir / "v02_imc25_temporal_positive.csv"
    locked_path = args.output_dir / "v02_primary_locked.csv"

    dev.to_csv(dev_path, index=False)
    imc_temporal[
        [c for c in keep + optional if c in imc_temporal.columns]
    ].to_csv(temporal_path, index=False)
    primary_locked[keep].to_csv(locked_path, index=False)

    summary = {
        "temporal_quantile": args.temporal_quantile,
        "cutoff": str(cutoff),
        "primary_development_rows": int(len(primary_dev)),
        "primary_development_class_counts": {
            str(k): int(v)
            for k, v in primary_dev["target"].value_counts().sort_index().items()
        },
        "primary_locked_rows": int(len(primary_locked)),
        "imc25_early_template_representatives": int(len(imc_early)),
        "imc25_temporal_template_representatives": int(len(imc_temporal)),
        "imc25_rows_removed_due_primary_locked_overlap": int(len(overlap_locked)),
        "v02_development_rows": int(len(dev)),
        "v02_development_class_counts": {
            str(k): int(v)
            for k, v in dev["target"].value_counts().sort_index().items()
        },
        "outputs": {
            "development": str(dev_path),
            "temporal_positive": str(temporal_path),
            "primary_locked": str(locked_path),
        },
    }

    (args.output_dir / "v02_corpus_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
