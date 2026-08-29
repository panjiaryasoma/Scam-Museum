from dataclasses import dataclass

from app.core.evidence_context import detect_contextual_evidence
from app.core.service import ScamAnalysisService


CRYPTO_SAMPLE = (
    "Many people know bitcoin, but they don't know what Ethereum is. "
    "I think you can share with me and learn the knowledge of mining and "
    "financial management in the future. My WhatsApp contact information "
    "is: +1 (952) 7693864 httpi/ivia.me/1952 7693864"
)

JOB_SAMPLE = (
    "May I share the job information with you? Great. We are Big Mover "
    "Company LLC. Your role is to write Google reviews for us. "
    "Each review pays $10."
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
    evidence = detect_contextual_evidence(CRYPTO_SAMPLE)
    ids = {item.id for item in evidence}

    assert "INVESTMENT_OR_CRYPTO_PITCH" in ids
    assert "OFF_PLATFORM_CONTACT_REQUEST" in ids


def test_crypto_pitch_with_private_contact_becomes_suspicious_not_high_risk():
    result = ScamAnalysisService(scorer=FakeScorer()).analyze_message(CRYPTO_SAMPLE)
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


def test_paid_review_job_pitch_emits_two_contextual_findings():
    evidence = detect_contextual_evidence(JOB_SAMPLE)
    ids = {item.id for item in evidence}

    assert "JOB_OR_TASK_SOLICITATION" in ids
    assert "PIECE_RATE_TASK_PAYMENT" in ids


def test_paid_review_job_pitch_becomes_suspicious():
    result = ScamAnalysisService(scorer=FakeScorer()).analyze_message(JOB_SAMPLE)
    ids = {item["id"] for item in result["evidence"]}

    assert "JOB_OR_TASK_SOLICITATION" in ids
    assert "PIECE_RATE_TASK_PAYMENT" in ids
    assert result["verdict"] == "SUSPICIOUS"
    assert result["exhibit"]["title"] == "THE PAID TASK PITCH"


def test_remote_microtask_offer_with_telegram_is_contextualized():
    result = ScamAnalysisService(scorer=FakeScorer()).analyze_message(
        "hey! saw your profile and we have easy remote work. like 3 videos "
        "a day and earn $200-500. message our manager on telegram "
        "@workteam88 to start"
    )
    ids = {item["id"] for item in result["evidence"]}

    assert "JOB_OR_TASK_SOLICITATION" in ids
    assert "PIECE_RATE_TASK_PAYMENT" in ids
    assert "OFF_PLATFORM_CONTACT_REQUEST" in ids
    assert result["verdict"] == "SUSPICIOUS"


def test_ordinary_job_description_is_not_a_paid_microtask_solicitation():
    evidence = detect_contextual_evidence(
        "We are hiring a software engineer. The role includes API design, "
        "testing, code review, and documentation. Salary is discussed during "
        "the interview process."
    )

    assert evidence == []
