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

JOB_TERMS = (
    r"\b(?:job(?:\s+(?:information|opportunity|offer))?|"
    r"work(?:\s+opportunity)?|role|position|remote\s+work)\b"
)

MICROTASK_TERMS = (
    r"\b(?:reviews?|ratings?|videos?|tasks?|orders?|products?|clicks?|"
    r"surveys?|apps?)\b"
)

JOB_TASK_PITCH_RE = re.compile(
    rf"(?:{JOB_TERMS}.{{0,260}}{MICROTASK_TERMS}|"
    rf"{MICROTASK_TERMS}.{{0,260}}{JOB_TERMS})",
    flags=re.IGNORECASE | re.DOTALL,
)

PAID_MICROTASK_RE = re.compile(
    r"(?:\b(?:each|per)\s+(?:review|rating|task|video|order|click|survey)s?"
    r"\s+(?:pays?|earns?|makes?|is)\s*[$£€]\s?\d+(?:[.,]\d+)?\b"
    r"|\b(?:like|review|rate|watch|click|complete|do)\b.{0,80}\b"
    r"(?:videos?|reviews?|ratings?|tasks?|orders?|products?|surveys?)\b"
    r".{0,120}\b(?:earn|make|get\s+paid|pays?)\b.{0,45}"
    r"[$£€]\s?\d+(?:[.,]\d+)?(?:\s*[-–]\s*[$£€]?\s?\d+(?:[.,]\d+)?)?)",
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

    The rules intentionally require combinations instead of treating isolated
    words such as "crypto", "job", "WhatsApp", or a dollar amount as scam
    evidence by themselves.
    """

    evidence: list[Evidence] = []
    solicitation_context = False

    pitch_match = INVESTMENT_PITCH_RE.search(text)
    if pitch_match is not None:
        solicitation_context = True
        evidence.append(
            _as_evidence(
                "INVESTMENT_OR_CRYPTO_PITCH",
                "manipulation",
                "supporting",
                pitch_match,
                "Frames crypto, investing, trading, or financial activity as a solicitation or opportunity.",
            )
        )

    job_match = JOB_TASK_PITCH_RE.search(text)
    paid_task_match = PAID_MICROTASK_RE.search(text)

    if job_match is not None and paid_task_match is not None:
        solicitation_context = True
        evidence.append(
            _as_evidence(
                "JOB_OR_TASK_SOLICITATION",
                "contextual",
                "supporting",
                job_match,
                "Frames simple online activity as a job, role, or work opportunity.",
            )
        )
        evidence.append(
            _as_evidence(
                "PIECE_RATE_TASK_PAYMENT",
                "operational",
                "supporting",
                paid_task_match,
                "Promises direct payment or earnings for individual low-friction online tasks.",
            )
        )

    if solicitation_context:
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
