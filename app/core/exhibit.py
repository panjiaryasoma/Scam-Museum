from __future__ import annotations


TITLE_RULES = [
    ({"OTP_REQUEST", "ACCOUNT_THREAT"}, "THE VERIFICATION TRAP"),
    ({"CREDENTIAL_REQUEST", "ACCOUNT_THREAT"}, "THE ACCOUNT PANIC"),
    ({"MONEY_TRANSFER_REQUEST", "FAMILY_IMPERSONATION"}, "THE FAMILY EMERGENCY"),
    ({"MONEY_TRANSFER_REQUEST", "NEW_NUMBER_CLAIM"}, "THE NEW NUMBER REQUEST"),
    ({"SUSPICIOUS_URL", "TIME_URGENCY"}, "THE URGENCY TRAP"),
    ({"NEED_AND_GREED", "PAYMENT_REQUEST"}, "THE PRIZE WITH A PRICE"),
]


def build_exhibit(analysis: dict, original_text: str) -> dict:
    evidence_ids = {item["id"] for item in analysis.get("evidence", [])}

    title = "UNCLASSIFIED ARTIFACT"
    for required, candidate in TITLE_RULES:
        if required.issubset(evidence_ids):
            title = candidate
            break

    if analysis["verdict"] == "INSUFFICIENT EVIDENCE":
        title = "AN INCOMPLETE ARTIFACT"
    elif analysis["verdict"] == "LOW RISK" and not evidence_ids:
        title = "NO CLEAR DECEPTION PATTERN"

    return {
        "title": title,
        "verdict": analysis["verdict"],
        "artifact_text": original_text,
        "ml_signal": analysis["ml_signal"],
        "evidence": analysis["evidence"],
        "protective_evidence": analysis["protective_evidence"],
        "curatorial_note": _curatorial_note(analysis),
    }


def _curatorial_note(analysis: dict) -> str:
    verdict = analysis["verdict"]

    if verdict == "HIGH RISK":
        return (
            "This message combines multiple observable scam behaviors. "
            "Avoid acting on the request until it is independently verified."
        )

    if verdict == "SUSPICIOUS":
        return (
            "This message contains meaningful risk signals, but the text alone "
            "does not verify the sender's real-world intent."
        )

    if verdict == "INSUFFICIENT EVIDENCE":
        return (
            "This message is ambiguous in isolation. More conversation context "
            "or independent verification is needed."
        )

    return (
        "No material scam request was detected in this message. "
        "This does not verify the sender or guarantee safety."
    )
