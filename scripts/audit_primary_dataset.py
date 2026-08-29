#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

LABEL_MAP = {
    "ham": ("LEGITIMATE", 0),
    "smishing": ("SCAM_RISK", 1),
    "spam": ("AMBIGUOUS_SPAM", None),
}

URL_RE = re.compile(r"""(?ix)
\b(
    (?:https?://|www\.)[^\s<>"']+
    |
    [a-z0-9.-]+\.(?:com|net|org|co|io|ly|me|uk|us|info|biz|app|site|online)
    (?:/[^\s<>"']*)?
)
""")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
LONG_NUM_RE = re.compile(r"(?<!\w)(?:[$£€₹]\s*)?\d[\d,.\s]{2,}\d(?!\w)")
WS_RE = re.compile(r"\s+")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_robust(path: Path) -> tuple[pd.DataFrame, str]:
    attempts = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    last_err = None
    for enc in attempts:
        try:
            return pd.read_csv(path, encoding=enc), enc
        except UnicodeDecodeError as exc:
            last_err = exc
    raise RuntimeError(f"Could not decode {path}: {last_err}")


def normalize_text_for_exact(value: str) -> str:
    value = html.unescape(str(value))
    value = unicodedata.normalize("NFKC", value)
    value = WS_RE.sub(" ", value).strip()
    return value


def canonical_template(value: str) -> str:
    value = normalize_text_for_exact(value).lower()
    value = EMAIL_RE.sub(" <EMAIL> ", value)
    value = URL_RE.sub(" <URL> ", value)
    value = PHONE_RE.sub(" <PHONE> ", value)
    value = LONG_NUM_RE.sub(" <NUMBER> ", value)
    value = WS_RE.sub(" ", value).strip()
    return value


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--processed-dir", default=Path("data/processed"), type=Path)
    ap.add_argument("--reports-dir", default=Path("reports"), type=Path)
    args = ap.parse_args()

    args.processed_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    df, encoding = read_csv_robust(args.input)
    df.columns = [str(c).strip().upper() for c in df.columns]

    required = {"LABEL", "TEXT"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise SystemExit(f"Missing columns: {sorted(missing_cols)}")

    raw_rows = len(df)
    df["source_label_raw"] = df["LABEL"].astype(str)
    df["source_label"] = (
        df["source_label_raw"].str.strip().str.casefold()
    )
    unknown_labels = sorted(set(df["source_label"]) - set(LABEL_MAP))

    df["text_raw"] = df["TEXT"]
    df["text_missing"] = df["TEXT"].isna()
    df["text"] = df["TEXT"].fillna("").astype(str).map(normalize_text_for_exact)
    df["text_empty"] = df["text"].str.len().eq(0)
    df["replacement_char_count"] = df["text"].str.count("\ufffd")

    mapped = df["source_label"].map(
        lambda x: LABEL_MAP.get(x, ("UNKNOWN", None))[0]
    )
    target = df["source_label"].map(
        lambda x: LABEL_MAP.get(x, ("UNKNOWN", None))[1]
    )
    df["canonical_label"] = mapped
    df["target"] = target

    df["exact_key"] = df["text"].map(lambda x: short_hash(x.casefold()))
    df["template"] = df["text"].map(canonical_template)
    df["template_group_id"] = df["template"].map(short_hash)

    # Exact duplicate diagnostics
    exact_sizes = df.groupby("exact_key").size().sort_values(ascending=False)
    duplicate_groups = exact_sizes[exact_sizes > 1]

    conflict_by_exact = (
        df[df["canonical_label"].isin(["LEGITIMATE", "SCAM_RISK"])]
        .groupby("exact_key")["canonical_label"]
        .nunique()
    )
    conflict_keys = set(conflict_by_exact[conflict_by_exact > 1].index)

    # Binary primary subset
    binary = df[df["canonical_label"].isin(["LEGITIMATE", "SCAM_RISK"])].copy()
    binary_before = len(binary)

    conflict_rows = binary["exact_key"].isin(conflict_keys)
    binary = binary[~conflict_rows].copy()
    conflict_rows_removed = int(conflict_rows.sum())

    # Remove same-label exact duplicates; keep first representative.
    before_exact_dedup = len(binary)
    binary = binary.drop_duplicates(subset=["exact_key"], keep="first").copy()
    exact_duplicate_rows_removed = before_exact_dedup - len(binary)

    binary["target"] = binary["canonical_label"].map(
        {"LEGITIMATE": 0, "SCAM_RISK": 1}
    ).astype(int)

    binary_output = args.processed_dir / "primary_binary_clean.csv"
    keep_cols = [
        "text",
        "target",
        "canonical_label",
        "source_label",
        "exact_key",
        "template_group_id",
    ]
    binary[keep_cols].to_csv(binary_output, index=False)

    spam = df[df["canonical_label"].eq("AMBIGUOUS_SPAM")].copy()
    spam_output = args.processed_dir / "ambiguous_spam.csv"
    spam[["text", "source_label", "exact_key", "template_group_id"]].to_csv(
        spam_output, index=False
    )

    label_counts = df["source_label"].value_counts(dropna=False).to_dict()
    canonical_counts = df["canonical_label"].value_counts(dropna=False).to_dict()
    clean_counts = binary["canonical_label"].value_counts().to_dict()

    template_sizes = binary.groupby("template_group_id").size().sort_values(ascending=False)
    repeated_template_groups = template_sizes[template_sizes > 1]

    report = {
        "input": str(args.input),
        "input_sha256": sha256_file(args.input),
        "encoding_used": encoding,
        "raw_rows": raw_rows,
        "columns": list(df.columns),
        "unknown_normalized_labels": unknown_labels,
        "source_label_counts_normalized": {str(k): int(v) for k, v in label_counts.items()},
        "canonical_label_counts": {str(k): int(v) for k, v in canonical_counts.items()},
        "missing_text_rows": int(df["text_missing"].sum()),
        "empty_text_rows_after_normalization": int(df["text_empty"].sum()),
        "rows_with_replacement_character": int((df["replacement_char_count"] > 0).sum()),
        "total_replacement_characters": int(df["replacement_char_count"].sum()),
        "exact_duplicate_group_count_all_labels": int(len(duplicate_groups)),
        "exact_duplicate_extra_rows_all_labels": int((duplicate_groups - 1).sum()) if len(duplicate_groups) else 0,
        "binary_rows_before_conflict_filter": binary_before,
        "binary_conflicting_exact_group_count": int(len(conflict_keys)),
        "binary_conflicting_rows_removed": conflict_rows_removed,
        "binary_same_label_exact_duplicate_rows_removed": int(exact_duplicate_rows_removed),
        "binary_rows_after_cleaning": int(len(binary)),
        "binary_clean_class_counts": {str(k): int(v) for k, v in clean_counts.items()},
        "binary_unique_template_groups": int(binary["template_group_id"].nunique()),
        "binary_repeated_template_group_count": int(len(repeated_template_groups)),
        "largest_binary_template_groups": [
            {"template_group_id": str(idx), "rows": int(size)}
            for idx, size in template_sizes.head(15).items()
        ],
        "outputs": {
            "primary_binary_clean": str(binary_output),
            "ambiguous_spam": str(spam_output),
        },
    }

    audit_json = args.reports_dir / "primary_audit.json"
    audit_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# Scam Museum — Primary Dataset Audit",
        "",
        f"- Raw rows: **{report['raw_rows']:,}**",
        f"- Encoding used: `{report['encoding_used']}`",
        f"- Missing text rows: **{report['missing_text_rows']:,}**",
        f"- Empty normalized text rows: **{report['empty_text_rows_after_normalization']:,}**",
        f"- Rows containing replacement character `�`: **{report['rows_with_replacement_character']:,}**",
        f"- Exact duplicate groups (all labels): **{report['exact_duplicate_group_count_all_labels']:,}**",
        f"- Conflicting exact groups (binary labels): **{report['binary_conflicting_exact_group_count']:,}**",
        f"- Same-label exact duplicate rows removed from binary pool: **{report['binary_same_label_exact_duplicate_rows_removed']:,}**",
        f"- Final binary rows: **{report['binary_rows_after_cleaning']:,}**",
        f"- Unique template groups: **{report['binary_unique_template_groups']:,}**",
        "",
        "## Normalized Source Labels",
        "",
    ]
    for k, v in sorted(report["source_label_counts_normalized"].items()):
        md.append(f"- `{k}`: {v:,}")
    md.extend(["", "## Final Binary Classes", ""])
    for k, v in sorted(report["binary_clean_class_counts"].items()):
        md.append(f"- `{k}`: {v:,}")
    md.extend([
        "",
        "## Notes",
        "",
        "- `Spam` is intentionally excluded from primary binary training.",
        "- Exact label conflicts are quarantined rather than majority-voted.",
        "- Canonical templates are used for group-aware splitting, not as runtime model input.",
    ])
    (args.reports_dir / "primary_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
