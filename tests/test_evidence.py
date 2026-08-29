import pytest

from app.core.evidence import detect_evidence


@pytest.mark.parametrize(
    "text,expected_id",
    [
        ("Send us your OTP immediately.", "OTP_REQUEST"),
        ("Provide your password to restore access.", "CREDENTIAL_REQUEST"),
        ("Transfer £900 today.", "MONEY_TRANSFER_REQUEST"),
        ("Your account will be suspended immediately.", "ACCOUNT_THREAT"),
        ("You won a prize. Claim your reward now.", "NEED_AND_GREED"),
        ("Hi Mum, this is my new number.", "FAMILY_IMPERSONATION"),
        ("Hi Mum, this is my new number.", "NEW_NUMBER_CLAIM"),
        ("Hi, is this Sarah?", "UNEXPECTED_CONTACT"),
    ],
)
def test_detects_expected_evidence(text, expected_id):
    evidence, _ = detect_evidence(text)
    assert expected_id in {item.id for item in evidence}


def test_legitimate_otp_warning_is_protective_not_request():
    evidence, protective = detect_evidence(
        "Your OTP is 482193. Do not share your OTP with anyone."
    )
    assert "OTP_REQUEST" not in {item.id for item in evidence}
    assert "PROTECTIVE_DO_NOT_SHARE" in {item.id for item in protective}


def test_shortener_is_suspicious():
    evidence, _ = detect_evidence("Verify at https://bit.ly/example")
    assert "SUSPICIOUS_URL" in {item.id for item in evidence}


def test_normal_url_not_automatically_suspicious():
    evidence, _ = detect_evidence(
        "Track your parcel at https://amazon.com/orders"
    )
    assert "SUSPICIOUS_URL" not in {item.id for item in evidence}


def test_evidence_span_matches_source_text():
    text = "Your account will be suspended immediately."
    evidence, _ = detect_evidence(text)
    item = next(x for x in evidence if x.id == "ACCOUNT_THREAT")
    assert text[item.start:item.end] == item.matched_text
