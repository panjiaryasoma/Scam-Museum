#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", default=Path("data/processed/split_manifest.csv"), type=Path)
    ap.add_argument("--fold", type=int, default=0, help="Locked test fold index [0..4]")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    required = {"text", "target", "template_group_id"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns: {sorted(missing)}")

    if not 0 <= args.fold <= 4:
        raise SystemExit("--fold must be between 0 and 4")

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    y = df["target"].astype(int)
    groups = df["template_group_id"].astype(str)

    selected = None
    for fold_idx, (dev_idx, test_idx) in enumerate(sgkf.split(df, y, groups)):
        if fold_idx == args.fold:
            selected = (dev_idx, test_idx)
            break

    if selected is None:
        raise RuntimeError("Could not create requested fold")

    dev_idx, test_idx = selected
    manifest = df.copy()
    manifest["split"] = "development"
    manifest.loc[test_idx, "split"] = "locked_test"

    dev_groups = set(manifest.loc[manifest["split"] == "development", "template_group_id"].astype(str))
    test_groups = set(manifest.loc[manifest["split"] == "locked_test", "template_group_id"].astype(str))
    overlap = dev_groups & test_groups
    if overlap:
        raise AssertionError(f"Group leakage detected: {len(overlap)} groups")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.output, index=False)

    print("Wrote:", args.output)
    print(manifest.groupby(["split", "target"]).size())
    print("Group overlap:", len(overlap))


if __name__ == "__main__":
    main()
