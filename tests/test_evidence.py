import pytest

from app.core.evidence import detect_evidence


@pytest.mark.parametrize(
    "text,expected_id",
    [
        ("Send us your OTP immediately.", "OTP_REQUEST"),
        (
            "Provide your password to restore access.",
            "CREDENTIAL_REQUEST",
        ),
        ("Transfer £900 today.", "MONEY_TRANSFER_REQUEST"),
        (
            "Your account will be suspended immediately.",
            "ACCOUNT_THREAT",
        ),
        (
            "You won a prize. Claim your reward now.",
            "NEED_AND_GREED",
        ),
        (
            "Hi Mum, this is my new number.",
            "FAMILY_IMPERSONATION",
        ),
        (
            "Hi Mum, this is my new number.",
            "NEW_NUMBER_CLAIM",
        ),
        ("Hi, is this Sarah?", "UNEXPECTED_CONTACT"),

        # Realistic-chat hardening cases.
        (
            "Reply YES and send the 6 digit code we just texted you.",
            "OTP_REQUEST",
        ),
        (
            "Need £650 for the repair guy asap, "
            "can you transfer it now?",
            "MONEY_TRANSFER_REQUEST",
        ),
        (
            "Need 5 Apple gift cards. Buy them now and "
            "send me pics of the codes.",
            "GIFT_CARD_REQUEST",
        ),
        (
            "Your account will close in 30 minutes.",
            "TIME_URGENCY",
        ),
        (
            "The network fee of $180 needs paying first.",
            "PAYMENT_REQUEST",
        ),
        (
            "We recovered the crypto you lost last year.",
            "RECOVERY_LURE",
        ),
        (
            "Please download and check the digital invoice attached below. "
            "Attachment: Delivery_Invoice.apk",
            "RISKY_ATTACHMENT",
        ),
        (
            "Might it be okey if you pay the payment until I get back "
            "into my banking?",
            "PAYMENT_REQUEST",
        ),
    ],
)
def test_detects_expected_evidence(
    text,
    expected_id,
):
    evidence, _ = detect_evidence(text)
    assert expected_id in {
        item.id for item in evidence
    }


def test_legitimate_otp_warning_is_protective_not_request():
    evidence, protective = detect_evidence(
        "Your OTP is 482193. "
        "Do not share your OTP with anyone."
    )
    assert "OTP_REQUEST" not in {
        item.id for item in evidence
    }
    assert "PROTECTIVE_DO_NOT_SHARE" in {
        item.id for item in protective
    }


def test_shortener_is_suspicious():
    evidence, _ = detect_evidence(
        "Verify at https://bit.ly/example"
    )
    assert "SUSPICIOUS_URL" in {
        item.id for item in evidence
    }


def test_normal_url_not_automatically_suspicious():
    evidence, _ = detect_evidence(
        "Track your parcel at "
        "https://amazon.com/orders"
    )
    assert "SUSPICIOUS_URL" not in {
        item.id for item in evidence
    }


def test_evidence_span_matches_source_text():
    text = (
        "Your account will be suspended immediately."
    )
    evidence, _ = detect_evidence(text)
    item = next(
        x
        for x in evidence
        if x.id == "ACCOUNT_THREAT"
    )
    assert (
        text[item.start:item.end]
        == item.matched_text
    )


def test_wifi_password_is_not_account_credential_request():
    evidence, _ = detect_evidence(
        "Can you send me the wifi password "
        "when you get home?"
    )
    assert "CREDENTIAL_REQUEST" not in {
        item.id for item in evidence
    }


def test_money_request_is_observable_but_not_critical_by_itself():
    evidence, _ = detect_evidence(
        "Can you send me the $18 from dinner "
        "when you get a sec?"
    )
    item = next(
        x
        for x in evidence
        if x.id == "MONEY_TRANSFER_REQUEST"
    )
    assert item.strength == "strong"


def test_card_details_is_financial_info_request():
    evidence, _ = detect_evidence(
        "Open this link to receive the money and enter your card details."
    )
    assert "FINANCIAL_INFO_REQUEST" in {item.id for item in evidence}


def test_family_reference_without_impersonation_context_is_not_flagged():
    evidence, _ = detect_evidence(
        "Hey Mum, dinner is at 7 tonight. "
        "I'll probably get there around 6:45."
    )
    assert "FAMILY_IMPERSONATION" not in {item.id for item in evidence}


def test_gift_card_request_is_not_reward_lure_or_money_transfer():
    evidence, _ = detect_evidence(
        "Hey, are you free? I'm stuck in a client meeting and need five "
        "Apple gift cards for the team. £100 each. Please buy them now "
        "and send me clear photos of the codes. I'll reimburse you later."
    )
    ids = {item.id for item in evidence}
    assert "GIFT_CARD_REQUEST" in ids
    assert "NEED_AND_GREED" not in ids
    assert "MONEY_TRANSFER_REQUEST" not in ids


def test_ocr_like_payment_request_is_detected_with_new_phone_context():
    evidence, _ = detect_evidence(
        "I was just trying to order a new phone but it wont let me do it. "
        "That's because the notification number goes to my old number. "
        "Might it be okey if you pay the payment until I get back into "
        "my banking? That will be on Saturday"
    )
    ids = {item.id for item in evidence}
    assert "NEW_NUMBER_CLAIM" in ids
    assert "PAYMENT_REQUEST" in ids
