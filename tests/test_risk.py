import pytest

from app.core.evidence import detect_evidence
from app.core.risk import decide_risk


def analyze(text, ml_label="WEAK"):
    score = {"WEAK": 0.10, "ELEVATED": 0.65, "STRONG": 0.85}[ml_label]
    evidence, protective = detect_evidence(text)
    return decide_risk(
        {
            "label": ml_label,
            "score": score,
            "model_version": "test",
            "threshold": 0.80,
        },
        evidence,
        protective,
    )


@pytest.mark.parametrize(
    "text,ml_label,expected",
    [
        (
            "Your OTP is 482193. Do not share your OTP with anyone.",
            "STRONG",
            "LOW RISK",
        ),
        (
            "Your account will be suspended immediately. "
            "Send us your OTP to verify your account.",
            "WEAK",
            "HIGH RISK",
        ),
        ("Hi, is this Sarah?", "WEAK", "INSUFFICIENT EVIDENCE"),
        ("Hi Mum, this is my new number.", "WEAK", "INSUFFICIENT EVIDENCE"),
        (
            "Hi Mum, this is my new number. Please send £900 today.",
            "WEAK",
            "HIGH RISK",
        ),
        (
            "Bank security team: your account is locked. "
            "Provide your password immediately to restore access.",
            "WEAK",
            "HIGH RISK",
        ),
        ("Dinner is at seven. See you at home.", "WEAK", "LOW RISK"),
        (
            "A security-related notification was generated.",
            "STRONG",
            "SUSPICIOUS",
        ),
        (
            "Your account is locked. Verify immediately at "
            "https://bit.ly/example",
            "WEAK",
            "HIGH RISK",
        ),
    ],
)
def test_locked_decision_contract(text, ml_label, expected):
    assert analyze(text, ml_label)["verdict"] == expected


def test_strong_ml_alone_never_means_high_risk():
    assert analyze(
        "A security-related notification was generated.", "STRONG"
    )["verdict"] != "HIGH RISK"


def test_reason_code_is_returned():
    result = analyze(
        "Your account will be suspended immediately. "
        "Send us your OTP to verify your account."
    )
    assert result["reason_codes"]
