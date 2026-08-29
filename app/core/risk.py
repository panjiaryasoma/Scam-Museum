from __future__ import annotations

from dataclasses import asdict

from .evidence import Evidence


CRITICAL = {
    "OTP_REQUEST",
    "CREDENTIAL_REQUEST",
    "FINANCIAL_INFO_REQUEST",
    "MONEY_TRANSFER_REQUEST",
}

STRONG = {
    "PAYMENT_REQUEST",
    "SUSPICIOUS_URL",
    "ACCOUNT_THREAT",
}

AMBIGUOUS_ONLY = {
    "FAMILY_IMPERSONATION",
    "NEW_NUMBER_CLAIM",
    "UNEXPECTED_CONTACT",
}


def decide_risk(
    ml_signal: dict,
    evidence: list[Evidence],
    protective_evidence: list[Evidence],
) -> dict:
    ids = {item.id for item in evidence}
    protective_ids = {item.id for item in protective_evidence}

    critical = ids & CRITICAL
    strong = ids & STRONG
    nonweak_positive = {
        item.id for item in evidence if item.strength != "weak"
    }

    if len(critical) >= 2:
        verdict = "HIGH RISK"
        reason_codes = ["MULTIPLE_CRITICAL_REQUESTS"]

    elif critical and (strong or (nonweak_positive - critical)):
        verdict = "HIGH RISK"
        reason_codes = ["CRITICAL_REQUEST_WITH_SUPPORTING_EVIDENCE"]

    elif {
        "SUSPICIOUS_URL",
        "ACCOUNT_THREAT",
        "TIME_URGENCY",
    }.issubset(ids):
        verdict = "HIGH RISK"
        reason_codes = ["THREAT_URGENCY_SUSPICIOUS_URL_COMBINATION"]

    elif (
        "MONEY_TRANSFER_REQUEST" in ids
        and (
            "FAMILY_IMPERSONATION" in ids
            or "NEW_NUMBER_CLAIM" in ids
        )
    ):
        verdict = "HIGH RISK"
        reason_codes = ["FAMILY_OR_NEW_NUMBER_MONEY_REQUEST"]

    elif protective_ids and not critical and not strong:
        verdict = "LOW RISK"
        reason_codes = ["PROTECTIVE_LANGUAGE_WITHOUT_ACTIONABLE_RISK"]

    elif len(critical) == 1:
        verdict = "SUSPICIOUS"
        reason_codes = ["SINGLE_CRITICAL_REQUEST"]

    # Context-only combinations remain ambiguous even if two contextual
    # indicators are present (e.g. "Mum" + "new number").
    elif ids and ids.issubset(AMBIGUOUS_ONLY):
        verdict = "INSUFFICIENT EVIDENCE"
        reason_codes = ["AMBIGUOUS_CONTEXT_ONLY"]

    elif len(nonweak_positive) >= 2:
        verdict = "SUSPICIOUS"
        reason_codes = ["MULTIPLE_OBSERVABLE_RISK_SIGNALS"]

    elif ml_signal.get("label") == "STRONG" and evidence:
        verdict = "SUSPICIOUS"
        reason_codes = ["ML_STRONG_WITH_OBSERVABLE_EVIDENCE"]

    elif ml_signal.get("label") == "STRONG" and not protective_ids:
        verdict = "SUSPICIOUS"
        reason_codes = ["ML_STRONG_WITH_LIMITED_DETERMINISTIC_EVIDENCE"]

    elif (
        ids
        and not critical
        and not strong
        and all(item.strength == "weak" for item in evidence)
    ):
        verdict = "INSUFFICIENT EVIDENCE"
        reason_codes = ["WEAK_CONTEXT_ONLY"]

    else:
        verdict = "LOW RISK"
        reason_codes = ["NO_MATERIAL_ACTIONABLE_RISK_DETECTED"]

    return {
        "verdict": verdict,
        "ml_signal": ml_signal,
        "evidence": [asdict(item) for item in evidence],
        "protective_evidence": [
            asdict(item) for item in protective_evidence
        ],
        "reason_codes": reason_codes,
    }
