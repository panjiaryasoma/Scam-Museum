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


TEXT_CANDIDATES = [
    "text", "message", "sms", "content", "message_text", "text_message"
]
LABEL_CANDIDATES = [
    "label", "class", "target", "category", "type"
]
LANG_CANDIDATES = [
    "language", "lang"
]


def find_col(columns, candidates):
    lookup = {str(c).strip().casefold(): c for c in columns}
    for name in candidates:
        if name in lookup:
            return lookup[name]
    return None


def map_label(value):
    x = str(value).strip().casefold()
    positive = {
        "scam", "fraud", "fraudulent", "phishing", "smishing",
        "1", "true", "positive"
    }
    negative = {
        "ham", "legitimate", "legit", "non-scam", "non scam",
        "not scam", "0", "false", "negative"
    }
    if x in positive:
        return 1
    if x in negative:
        return 0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", default=Path(
        "data/processed/final_external_financial_english.csv"
    ), type=Path)
    ap.add_argument("--text-col")
    ap.add_argument("--label-col")
    ap.add_argument("--language-col")
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    print("Columns:", list(df.columns))

    text_col = args.text_col or find_col(df.columns, TEXT_CANDIDATES)
    label_col = args.label_col or find_col(df.columns, LABEL_CANDIDATES)
    lang_col = args.language_col or find_col(df.columns, LANG_CANDIDATES)

    if text_col is None or label_col is None:
        raise SystemExit(
            "Could not autodetect text/label columns. "
            "Pass --text-col and --label-col explicitly."
        )

    work = df.copy()

    if lang_col is not None:
        lang = work[lang_col].astype(str).str.strip().str.casefold()
        english_values = {
            "english", "en", "eng", "en-us", "en-gb"
        }
        work = work[lang.isin(english_values)].copy()
        print("English filtering using:", lang_col)
    else:
        print(
            "WARNING: no language column detected. "
            "No language filtering was applied."
        )

    work["target"] = work[label_col].map(map_label)
    unknown = sorted(
        set(
            work.loc[work["target"].isna(), label_col]
            .astype(str)
            .unique()
            .tolist()
        )
    )
    if unknown:
        print("Unmapped labels:", unknown[:30])

    work = work[work["target"].notna()].copy()
    work["target"] = work["target"].astype(int)

    work["text"] = (
        work[text_col]
        .fillna("")
        .astype(str)
        .map(normalize_model_text)
    )
    work = work[work["text"].str.len() > 0].copy()
    work["template"] = work["text"].map(canonical_template)
    work["template_group_id"] = work["template"].map(short_hash)

    # Conflicting exact/template labels are quarantined.
    conflicts = (
        work.groupby("template_group_id")["target"]
        .nunique()
    )
    conflict_ids = set(conflicts[conflicts > 1].index)
    conflict_rows = int(work["template_group_id"].isin(conflict_ids).sum())
    work = work[
        ~work["template_group_id"].isin(conflict_ids)
    ].copy()

    # One representative per template group.
    before_dedup = len(work)
    work = work.drop_duplicates("template_group_id").copy()
    dedup_removed = before_dedup - len(work)

    # Remove overlap with any training/development files.
    excluded_groups = set()
    for raw_path in args.exclude:
        path = Path(raw_path)
        if not path.exists():
            raise SystemExit(f"Exclude file not found: {path}")
        other = pd.read_csv(path)
        if "template_group_id" in other.columns:
            excluded_groups.update(
                other["template_group_id"].astype(str)
            )
        elif "text" in other.columns:
            excluded_groups.update(
                other["text"]
                .fillna("")
                .astype(str)
                .map(normalize_model_text)
                .map(canonical_template)
                .map(short_hash)
            )

    overlap_rows = int(
        work["template_group_id"].astype(str).isin(excluded_groups).sum()
    )
    work = work[
        ~work["template_group_id"].astype(str).isin(excluded_groups)
    ].copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    work[["text", "target", "template_group_id"]].to_csv(
        args.output,
        index=False,
    )

    summary = {
        "input": str(args.input),
        "text_column": str(text_col),
        "label_column": str(label_col),
        "language_column": None if lang_col is None else str(lang_col),
        "conflicting_rows_removed": conflict_rows,
        "duplicate_template_rows_removed": dedup_removed,
        "overlap_rows_removed": overlap_rows,
        "final_rows": int(len(work)),
        "class_counts": {
            str(k): int(v)
            for k, v in work["target"].value_counts().sort_index().items()
        },
        "output": str(args.output),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
