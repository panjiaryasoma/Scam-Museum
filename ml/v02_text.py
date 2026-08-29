from __future__ import annotations

import hashlib
import html
import re
import unicodedata

URL_RE = re.compile(
    r"""(?ix)
    \b(
        (?:https?://|www\.)[^\s<>"']+
        |
        [a-z0-9.-]+\.(?:com|net|org|co|io|ly|me|uk|us|info|biz|app|site|online)
        (?:/[^\s<>"']*)?
    )
    """
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)")
LONG_NUM_RE = re.compile(r"(?<!\w)(?:[$£€₹]\s*)?\d[\d,.\s]{2,}\d(?!\w)")
WS_RE = re.compile(r"\s+")

PLACEHOLDER_MAP = {
    "<PHONE_NUMBER>": "<PHONE>",
    "<US_DRIVER_LICENSE>": "<ID>",
    "<DATE_TIME>": "<DATE>",
    "<NAMED_ENTITY>": "<ENTITY>",
    "<LOCATION>": "<LOCATION>",
    "<NRP>": "<ENTITY>",
}


def normalize_model_text(value: str) -> str:
    value = html.unescape(str(value))
    value = unicodedata.normalize("NFKC", value)

    for src, dst in PLACEHOLDER_MAP.items():
        value = value.replace(src, dst)

    value = EMAIL_RE.sub(" <EMAIL> ", value)
    value = URL_RE.sub(" <URL> ", value)
    value = PHONE_RE.sub(" <PHONE> ", value)
    value = LONG_NUM_RE.sub(" <NUMBER> ", value)
    value = WS_RE.sub(" ", value).strip()
    return value


def canonical_template(value: str) -> str:
    return normalize_model_text(value).casefold()


def short_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8", errors="replace")
    ).hexdigest()[:16]
