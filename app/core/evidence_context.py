from __future__ import annotations

import re

from .evidence import Evidence


CRYPTO_TERMS = (
    r"\b(?:bitcoin|btc|ethereum|ether(?:eum)?|eth|crypto(?:currency|currencies)?|"
    r"blockchain|mining|wallet)\b"
)

PITCH_TERMS = (
    r"\b(?:invest(?:ment|ing)?|trad(?:e|ing)|profit|returns?|earn(?:ing|s)?|"
    r"financial management|share with me|learn (?:with|from) me|"
    r"join (?:me|us)|opportunit(?:y|ies))\b"
)

INVESTMENT_PITCH_RE = re.compile(
    rf"(?:{CRYPTO_TERMS}.{{0,320}}{PITCH_TERMS}|"
    rf"{PITCH_TERMS}.{{0,320}}{CRYPTO_TERMS})",
    flags=re.IGNORECASE | re.DOTALL,
)

OFF_PLATFORM_RE = re.compile(
    r"\b(?:whats?app|telegram|signal)\b.{0,100}"
    r"(?:contact(?: information)?|message|text|reach|dm|number|"
    r"@[A-Za-z0-9_.-]{3,}|\+?\d[\d\s().-]{6,})"
    r"|(?:contact|message|text|reach|dm)\b.{0,60}\b"
    r"(?:whats?app|telegram|signal)\b",
    flags=re.IGNORECASE | re.DOTALL,
)


def _as_evidence(
    evidence_id: str,
    category: str,
    strength: str,
    match: re.Match[str],
    rationale: str,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        category=category,
        strength=strength,
        matched_text=match.group(0),
        start=match.start(),
        end=match.end(),
        rationale=rationale,
    )


def detect_contextual_evidence(text: str) -> list[Evidence]:
    """Detect higher-context solicitation patterns conservatively.

    These rules intentionally require a crypto/investment pitch before an
    off-platform contact request is treated as material evidence. This avoids
    turning ordinary WhatsApp or Telegram mentions into scam findings.
    """

    pitch_match = INVESTMENT_PITCH_RE.search(text)
    if pitch_match is None:
        return []

    evidence = [
        _as_evidence(
            "INVESTMENT_OR_CRYPTO_PITCH",
            "manipulation",
            "supporting",
            pitch_match,
            "Frames crypto, investing, trading, or financial activity as a solicitation or opportunity.",
        )
    ]

    off_platform_match = OFF_PLATFORM_RE.search(text)
    if off_platform_match is not None:
        evidence.append(
            _as_evidence(
                "OFF_PLATFORM_CONTACT_REQUEST",
                "operational",
                "supporting",
                off_platform_match,
                "Moves the solicitation toward a private messaging or direct-contact channel.",
            )
        )

    evidence.sort(key=lambda item: (item.start, item.end, item.id))
    return evidence
