import pytest

from app.core.evidence import detect_evidence
from app.core.risk import decide_risk


def analyze(
    text,
    ml_label="WEAK",
):
    score = {
        "WEAK": 0.10,
        "ELEVATED": 0.65,
        "STRONG": 0.85,
    }[ml_label]

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
            "Your OTP is 482193. "
            "Do not share your OTP with anyone.",
            "STRONG",
            "LOW RISK",
        ),
        (
            "Your account will be suspended immediately. "
            "Send us your OTP to verify your account.",
            "WEAK",
            "HIGH RISK",
        ),
        (
            "Hi, is this Sarah?",
            "WEAK",
            "INSUFFICIENT EVIDENCE",
        ),
        (
            "Hi Mum, this is my new number.",
            "WEAK",
            "INSUFFICIENT EVIDENCE",
        ),
        (
            "Hi Mum, this is my new number. "
            "Please send £900 today.",
            "WEAK",
            "HIGH RISK",
        ),
        (
            "Bank security team: your account is locked. "
            "Provide your password immediately "
            "to restore access.",
            "WEAK",
            "HIGH RISK",
        ),
        (
            "Dinner is at seven. See you at home.",
            "WEAK",
            "LOW RISK",
        ),
        (
            "A security-related notification "
            "was generated.",
            "STRONG",
            "SUSPICIOUS",
        ),
        (
            "Your account is locked. "
            "Verify immediately at "
            "https://bit.ly/example",
            "WEAK",
            "HIGH RISK",
        ),
        (
            "We noticed something unusual on your account earlier today. "
            "Please review your recent activity when you have time.",
            "ELEVATED",
            "INSUFFICIENT EVIDENCE",
        ),

        # RC02
        (
            "Unknown: Hi Mum, new phone here\n"
            "Mum: who is this?\n"
            "Unknown: it's me, Sam. old phone died\n"
            "Unknown: need £650 for the repair guy asap, "
            "can you transfer it now?",
            "ELEVATED",
            "HIGH RISK",
        ),

        # RC03
        (
            "Hi, fraud team here. We blocked a £786 card payment. "
            "Reply YES and send the 6 digit code we just texted you "
            "so we can cancel it.",
            "STRONG",
            "HIGH RISK",
        ),

        # RC04
        (
            "parcel 8842 couldn't be delivered today. "
            "small £1.49 redelivery fee due: "
            "https://bit.ly/redeliver8842 "
            "pls sort before 6pm",
            "ELEVATED",
            "HIGH RISK",
        ),

        # RC05
        (
            "Boss: hey are you free?\n"
            "You: yep what's up\n"
            "Boss: stuck in a client meeting. "
            "need 5 apple gift cards for the team\n"
            "Boss: £100 each. buy them now and "
            "send me pics of the codes",
            "WEAK",
            "HIGH RISK",
        ),

        # RC08
        (
            "Good news, we recovered the crypto you lost last year. "
            "Wallet is ready to release 4.2 ETH, "
            "only the network fee of $180 needs paying first.",
            "WEAK",
            "HIGH RISK",
        ),

        # RC10
        (
            "SECURITY ALERT: unusual login detected. "
            "Your account will be closed in 30 minutes "
            "unless you verify now: "
            "https://bit.ly/account-check",
            "STRONG",
            "HIGH RISK",
        ),

        # RC17: money alone is observable, not automatically scam.
        (
            "hey can u send me the $18 from dinner "
            "when you get a sec? no rush",
            "WEAK",
            "LOW RISK",
        ),

        # RC18: household Wi-Fi password is not an account credential.
        (
            "can you send me the wifi password when you get home? "
            "i forgot to save it 😭",
            "WEAK",
            "LOW RISK",
        ),

        # RC07: elevated ML signal without observable evidence remains unresolved.
        (
            "hey! saw your profile and we have easy remote work. "
            "like 3 videos a day and earn $200-500. "
            "message our manager on telegram @workteam88 to start",
            "ELEVATED",
            "INSUFFICIENT EVIDENCE",
        ),
    ],
)
def test_locked_decision_contract(
    text,
    ml_label,
    expected,
):
    assert (
        analyze(text, ml_label)["verdict"]
        == expected
    )


def test_strong_ml_alone_never_means_high_risk():
    assert (
        analyze(
            "A security-related notification "
            "was generated.",
            "STRONG",
        )["verdict"]
        != "HIGH RISK"
    )


def test_elevated_ml_without_observable_evidence_is_unresolved():
    result = analyze(
        "We noticed something unusual on your account earlier today. "
        "Please review your recent activity when you have time.",
        "ELEVATED",
    )
    assert result["verdict"] == "INSUFFICIENT EVIDENCE"
    assert (
        "ML_ELEVATED_WITHOUT_OBSERVABLE_EVIDENCE"
        in result["reason_codes"]
    )


def test_reason_code_is_returned():
    result = analyze(
        "Your account will be suspended immediately. "
        "Send us your OTP to verify your account."
    )
    assert result["reason_codes"]
