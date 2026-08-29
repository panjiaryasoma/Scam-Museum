#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import re
import unicodedata
from pathlib import Path

import pandas as pd

WS_RE = re.compile(r"\s+")


def norm(x):
    x = html.unescape(str(x))
    x = unicodedata.normalize("NFKC", x)
    return WS_RE.sub(" ", x).strip()


def key(x):
    return hashlib.sha256(norm(x).casefold().encode("utf-8", errors="replace")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--primary-clean", type=Path)
    ap.add_argument("--output", default=Path("data/processed/imc25_english_challenge.csv"), type=Path)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"text", "language", "scam_type"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing expected IMC columns: {sorted(missing)}")

    eng = df[df["language"].astype(str).str.casefold().eq("english")].copy()
    eng = eng[~eng["scam_type"].astype(str).str.casefold().eq("spam")].copy()
    eng["text"] = eng["text"].fillna("").map(norm)
    eng = eng[eng["text"].str.len() > 0].copy()
    eng["exact_key"] = eng["text"].map(key)
    eng = eng.drop_duplicates(subset=["exact_key"]).copy()

    if args.primary_clean and args.primary_clean.exists():
        primary = pd.read_csv(args.primary_clean)
        primary_keys = set(primary["exact_key"].astype(str))
        eng = eng[~eng["exact_key"].isin(primary_keys)].copy()

    keep = [
        c for c in [
            "time", "text", "language", "scam_type", "lure_principles",
            "named_entity", "url_shortener", "exact_key"
        ] if c in eng.columns
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    eng[keep].to_csv(args.output, index=False)

    print("English non-spam challenge rows:", len(eng))
    print("\nScam types:")
    print(eng["scam_type"].value_counts().head(20))
    if "lure_principles" in eng.columns:
        print("\nLure annotation non-null:", int(eng["lure_principles"].notna().sum()))
    print("Wrote:", args.output)


if __name__ == "__main__":
    main()
