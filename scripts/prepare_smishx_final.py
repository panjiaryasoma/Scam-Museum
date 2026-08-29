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


def normalized_group(series):
    return (
        series.fillna("")
        .astype(str)
        .map(normalize_model_text)
        .map(canonical_template)
        .map(short_hash)
    )


def groups_from_file(path: Path):
    df = pd.read_csv(path)
    if "text" in df.columns:
        return set(normalized_group(df["text"]).astype(str))
    if "message" in df.columns:
        return set(normalized_group(df["message"]).astype(str))
    if "SMS" in df.columns:
        return set(normalized_group(df["SMS"]).astype(str))
    return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument(
        "--output",
        default=Path("data/processed/smishx_final_external.csv"),
        type=Path,
    )
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    required = {"SMS", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"SmishX missing: {sorted(missing)}")

    work = df.copy()
    work["label_norm"] = work["label"].astype(str).str.strip().str.casefold()

    mapping = {
        "legitimate": 0,
        "phishing": 1,
        "smishing": 1,
    }

    source_counts = work["label_norm"].value_counts().to_dict()

    work["target"] = work["label_norm"].map(mapping)
    excluded_spam_rows = int(work["label_norm"].eq("spam").sum())
    unmapped = sorted(
        work.loc[work["target"].isna() & ~work["label_norm"].eq("spam"), "label_norm"]
        .unique()
        .tolist()
    )
    if unmapped:
        raise SystemExit(f"Unexpected SmishX labels: {unmapped}")

    work = work[work["target"].notna()].copy()
    work["target"] = work["target"].astype(int)
    work["text"] = work["SMS"].fillna("").astype(str).map(normalize_model_text)
    work = work[work["text"].str.len() > 0].copy()
    work["template_group_id"] = work["text"].map(canonical_template).map(short_hash)

    conflicts = work.groupby("template_group_id")["target"].nunique()
    conflict_ids = set(conflicts[conflicts > 1].index.astype(str))
    conflict_rows = int(
        work["template_group_id"].astype(str).isin(conflict_ids).sum()
    )
    work = work[
        ~work["template_group_id"].astype(str).isin(conflict_ids)
    ].copy()

    before_dedup = len(work)
    work = work.drop_duplicates("template_group_id").copy()
    duplicate_rows_removed = before_dedup - len(work)

    excluded_groups = set()
    for path_str in args.exclude:
        excluded_groups |= groups_from_file(Path(path_str))

    overlap_mask = work["template_group_id"].astype(str).isin(excluded_groups)
    overlap_rows_removed = int(overlap_mask.sum())
    work = work[~overlap_mask].copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    work[["text", "target", "template_group_id"]].to_csv(
        args.output,
        index=False,
    )

    result = {
        "source_rows": int(len(df)),
        "source_label_counts": {
            str(k): int(v) for k, v in source_counts.items()
        },
        "spam_rows_excluded": excluded_spam_rows,
        "conflicting_rows_removed": conflict_rows,
        "duplicate_template_rows_removed": int(duplicate_rows_removed),
        "training_overlap_rows_removed": overlap_rows_removed,
        "final_rows": int(len(work)),
        "final_class_counts": {
            str(k): int(v)
            for k, v in work["target"].value_counts().sort_index().items()
        },
        "output": str(args.output),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
