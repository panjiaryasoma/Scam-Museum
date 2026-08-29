from dataclasses import dataclass

import pytest

from app.core.service import (
    AnalysisValidationError,
    MAX_MESSAGE_LENGTH,
    ScamAnalysisService,
)


@dataclass(frozen=True)
class FakeSignal:
    label: str
    score: float
    model_version: str = "test"
    threshold: float = 0.8

    def to_dict(self):
        return {
            "label": self.label,
            "score": self.score,
            "model_version": self.model_version,
            "threshold": self.threshold,
        }


class FakeScorer:
    def __init__(self, label="WEAK", score=0.10):
        self.label = label
        self.score = score
        self.seen = []

    def analyze(self, text):
        self.seen.append(text)
        return FakeSignal(
            label=self.label,
            score=self.score,
        )


def test_service_returns_complete_contract():
    service = ScamAnalysisService(
        scorer=FakeScorer(label="STRONG", score=0.91)
    )

    result = service.analyze_message(
        "Your account will be suspended immediately. "
        "Send us your OTP to verify your account."
    )

    assert result["verdict"] == "HIGH RISK"
    assert result["ml_signal"]["label"] == "STRONG"
    assert result["exhibit"]["verdict"] == "HIGH RISK"
    assert result["reason_codes"]
    assert result["meta"]["evidence_count"] >= 2


def test_service_trims_message_before_analysis():
    scorer = FakeScorer()
    service = ScamAnalysisService(scorer=scorer)

    result = service.analyze_message(
        "   Dinner is at seven.   "
    )

    assert scorer.seen == ["Dinner is at seven."]
    assert (
        result["exhibit"]["artifact_text"]
        == "Dinner is at seven."
    )


@pytest.mark.parametrize(
    "value,error_fragment",
    [
        ("", "must not be empty"),
        ("   ", "must not be empty"),
        (None, "must be a string"),
        (123, "must be a string"),
    ],
)
def test_service_rejects_invalid_message(
    value,
    error_fragment,
):
    service = ScamAnalysisService(scorer=FakeScorer())

    with pytest.raises(AnalysisValidationError) as exc:
        service.analyze_message(value)

    assert error_fragment in str(exc.value)


def test_service_rejects_oversized_message():
    service = ScamAnalysisService(scorer=FakeScorer())

    with pytest.raises(AnalysisValidationError):
        service.analyze_message(
            "x" * (MAX_MESSAGE_LENGTH + 1)
        )
