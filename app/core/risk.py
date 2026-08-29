from __future__ import annotations

import re
from dataclasses import asdict

from .evidence import Evidence


CRITICAL = {
    "OTP_REQUEST",
    "CREDENTIAL_REQUEST",
    "FINANCIAL_INFO_REQUEST",
    "GIFT_CARD_REQUEST",
    "RISKY_ATTACHMENT",
}

STRONG = {
    "MONEY_TRANSFER_REQUEST",
    "PAYMENT_REQUEST",
    "SUSPICIOUS_URL",
    "ACCOUNT_THREAT",
}

AMBIGUOUS_ONLY = {
    "FAMILY_IMPERSONATION",
    "NEW_NUMBER_CLAIM",
    "UNEXPECTED_CONTACT",
}

BENIGN_INFORMATIONAL_PATTERNS = (
    r"\b(?:order|parcel|package|shipment)\b.{0,60}\b"
    r"(?:has\s+(?:been\s+)?(?:shipped|delivered)|"
    r"was\s+(?:shipped|delivered)|delivered\s+successfully)\b",
    r"\bpassword\s+reset\b.{0,50}\b"
    r"(?:completed|successful(?:ly)?)\b",
)

BENIGN_MONEY_TRANSFER_PATTERNS = (
    r"\b(?:send|transfer|pay)\b.{0,35}\b"
    r"(?:from|for)\s+(?:dinner|lunch|coffee|groceries|tickets?|rent|utilities?)\b",
    r"\b(?:from|for)\s+(?:dinner|lunch|coffee|groceries|tickets?|rent|utilities?)\b"
    r".{0,35}\b(?:send|transfer|pay)\b",
    r"\b(?:pay|send|transfer)\s+(?:me|you)\s+back\b",
    r"\b(?:owe|owed)\s+(?:me|you)\b",
    r"\b(?:split|splitting)\s+(?:the\s+)?(?:bill|check|cost)\b",
    r"\breimburse(?:ment|d|s|ing)?\b",
)


def _has_benign_informational_context(text: str | None) -> bool:
    if not text:
        return False

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for pattern in BENIGN_INFORMATIONAL_PATTERNS
    )


def _has_benign_money_transfer_context(text: str | None) -> bool:
    if not text:
        return False

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for pattern in BENIGN_MONEY_TRANSFER_PATTERNS
    )


def decide_risk(
    ml_signal: dict,
    evidence: list[Evidence],
    protective_evidence: list[Evidence],
    text: str | None = None,
) -> dict:
    ids = {item.id for item in evidence}
    protective_ids = {
        item.id for item in protective_evidence
    }

    critical = ids & CRITICAL
    strong = ids & STRONG
    nonweak_positive = {
        item.id
        for item in evidence
        if item.strength != "weak"
    }
    benign_informational = _has_benign_informational_context(
        text
    )
    benign_money_transfer = _has_benign_money_transfer_context(
        text
    )

    if len(critical) >= 2:
        verdict = "HIGH RISK"
        reason_codes = [
            "MULTIPLE_CRITICAL_REQUESTS"
        ]

    elif "RISKY_ATTACHMENT" in critical:
        verdict = "HIGH RISK"
        reason_codes = [
            "EXECUTABLE_ATTACHMENT_INTERACTION_REQUEST"
        ]

    elif critical and (
        strong
        or (nonweak_positive - critical)
    ):
        verdict = "HIGH RISK"
        reason_codes = [
            "CRITICAL_REQUEST_WITH_SUPPORTING_EVIDENCE"
        ]

    elif {
        "SUSPICIOUS_URL",
        "ACCOUNT_THREAT",
        "TIME_URGENCY",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = [
            "THREAT_URGENCY_SUSPICIOUS_URL_COMBINATION"
        ]

    elif {
        "PAYMENT_REQUEST",
        "SUSPICIOUS_URL",
        "TIME_URGENCY",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = [
            "PAYMENT_URGENCY_SUSPICIOUS_URL_COMBINATION"
        ]

    elif {
        "MONEY_TRANSFER_REQUEST",
        "ACCOUNT_THREAT",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = [
            "MONEY_REQUEST_WITH_ACCOUNT_OR_SERVICE_THREAT"
        ]

    elif {
        "MONEY_TRANSFER_REQUEST",
        "TIME_URGENCY",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = [
            "MONEY_REQUEST_WITH_TIME_PRESSURE"
        ]

    elif (
        "MONEY_TRANSFER_REQUEST" in ids
        and (
            "FAMILY_IMPERSONATION" in ids
            or "NEW_NUMBER_CLAIM" in ids
        )
    ):
        verdict = "HIGH RISK"
        reason_codes = [
            "FAMILY_OR_NEW_NUMBER_MONEY_REQUEST"
        ]

    elif {
        "RECOVERY_LURE",
        "PAYMENT_REQUEST",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = [
            "RECOVERY_LURE_WITH_ADVANCE_PAYMENT"
        ]

    elif (
        protective_ids
        and not critical
        and not strong
    ):
        verdict = "LOW RISK"
        reason_codes = [
            "PROTECTIVE_LANGUAGE_WITHOUT_ACTIONABLE_RISK"
        ]

    elif len(critical) == 1:
        verdict = "SUSPICIOUS"
        reason_codes = [
            "SINGLE_CRITICAL_REQUEST"
        ]

    # Context-only combinations remain ambiguous.
    elif ids and ids.issubset(
        AMBIGUOUS_ONLY
    ):
        verdict = "INSUFFICIENT EVIDENCE"
        reason_codes = [
            "AMBIGUOUS_CONTEXT_ONLY"
        ]

    # A standalone request to move money is actionable, but not enough by
    # itself to call the sender deceptive. Preserve clearly ordinary repayment
    # language as low risk while keeping other money requests unresolved.
    elif nonweak_positive == {"MONEY_TRANSFER_REQUEST"}:
        if (
            benign_money_transfer
            and ml_signal.get("label") == "WEAK"
        ):
            verdict = "LOW RISK"
            reason_codes = [
                "BENIGN_REPAYMENT_CONTEXT_WITHOUT_ADDITIONAL_RISK"
            ]
        else:
            verdict = "INSUFFICIENT EVIDENCE"
            reason_codes = [
                "MONEY_TRANSFER_REQUEST_WITHOUT_DECEPTION_CONTEXT"
            ]

    elif len(nonweak_positive) >= 2:
        verdict = "SUSPICIOUS"
        reason_codes = [
            "MULTIPLE_OBSERVABLE_RISK_SIGNALS"
        ]

    elif (
        ml_signal.get("label") == "STRONG"
        and evidence
    ):
        verdict = "SUSPICIOUS"
        reason_codes = [
            "ML_STRONG_WITH_OBSERVABLE_EVIDENCE"
        ]

    elif (
        ml_signal.get("label") == "STRONG"
        and not protective_ids
    ):
        verdict = "SUSPICIOUS"
        reason_codes = [
            "ML_STRONG_WITH_LIMITED_DETERMINISTIC_EVIDENCE"
        ]

    elif (
        ml_signal.get("label") == "ELEVATED"
        and not ids
        and not protective_ids
        and benign_informational
    ):
        verdict = "LOW RISK"
        reason_codes = [
            "BENIGN_INFORMATIONAL_CONTEXT_WITHOUT_ACTIONABLE_RISK"
        ]

    elif (
        ml_signal.get("label") == "ELEVATED"
        and not ids
        and not protective_ids
    ):
        verdict = "INSUFFICIENT EVIDENCE"
        reason_codes = [
            "ML_ELEVATED_WITHOUT_OBSERVABLE_EVIDENCE"
        ]

    elif (
        ids
        and not critical
        and not strong
        and all(
            item.strength == "weak"
            for item in evidence
        )
    ):
        verdict = "INSUFFICIENT EVIDENCE"
        reason_codes = [
            "WEAK_CONTEXT_ONLY"
        ]

    else:
        verdict = "LOW RISK"
        reason_codes = [
            "NO_MATERIAL_ACTIONABLE_RISK_DETECTED"
        ]

    return {
        "verdict": verdict,
        "ml_signal": ml_signal,
        "evidence": [
            asdict(item)
            for item in evidence
        ],
        "protective_evidence": [
            asdict(item)
            for item in protective_evidence
        ],
        "reason_codes": reason_codes,
    }
