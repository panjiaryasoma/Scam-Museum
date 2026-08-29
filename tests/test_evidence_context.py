from dataclasses import dataclass

from app.core.evidence_context import detect_contextual_evidence
from app.core.service import ScamAnalysisService


SAMPLE = (
    "Many people know bitcoin, but they don't know what Ethereum is. "
    "I think you can share with me and learn the knowledge of mining and "
    "financial management in the future. My WhatsApp contact information "
    "is: +1 (952) 7693864 httpi/ivia.me/1952 7693864"
)


@dataclass(frozen=True)
class FakeSignal:
    label: str = "ELEVATED"
    score: float = 0.66
    model_version: str = "test"
    threshold: float = 0.80

    def to_dict(self):
        return {
            "label": self.label,
            "score": self.score,
            "model_version": self.model_version,
            "threshold": self.threshold,
        }


class FakeScorer:
    def analyze(self, text):
        return FakeSignal()


def test_crypto_pitch_with_private_contact_emits_two_contextual_findings():
    evidence = detect_contextual_evidence(SAMPLE)
    ids = {item.id for item in evidence}

    assert "INVESTMENT_OR_CRYPTO_PITCH" in ids
    assert "OFF_PLATFORM_CONTACT_REQUEST" in ids


def test_crypto_pitch_with_private_contact_becomes_suspicious_not_high_risk():
    result = ScamAnalysisService(scorer=FakeScorer()).analyze_message(SAMPLE)
    ids = {item["id"] for item in result["evidence"]}

    assert "INVESTMENT_OR_CRYPTO_PITCH" in ids
    assert "OFF_PLATFORM_CONTACT_REQUEST" in ids
    assert result["verdict"] == "SUSPICIOUS"
    assert result["exhibit"]["title"] == "THE INVESTMENT INVITATION"


def test_plain_crypto_education_is_not_a_contextual_solicitation():
    evidence = detect_contextual_evidence(
        "Bitcoin and Ethereum are cryptocurrencies. This chapter explains "
        "blockchain consensus and mining at a high level."
    )

    assert evidence == []


def test_non_crypto_telegram_job_message_keeps_existing_contract():
    result = ScamAnalysisService(scorer=FakeScorer()).analyze_message(
        "hey! saw your profile and we have easy remote work. like 3 videos "
        "a day and earn $200-500. message our manager on telegram "
        "@workteam88 to start"
    )

    assert result["verdict"] == "INSUFFICIENT EVIDENCE"
