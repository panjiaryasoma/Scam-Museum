from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol

from .evidence import detect_evidence
from .exhibit import build_exhibit
from .risk import decide_risk


MAX_MESSAGE_LENGTH = 5_000


class RiskSignal(Protocol):
    def to_dict(self) -> dict[str, Any]:
        ...


class RiskScorer(Protocol):
    def analyze(self, text: str) -> RiskSignal:
        ...


class AnalysisValidationError(ValueError):
    """Raised when user input violates the P0 analysis contract."""


class ScamAnalysisService:
    def __init__(self, scorer: RiskScorer | None = None) -> None:
        self._scorer = scorer

    @property
    def scorer(self) -> RiskScorer:
        if self._scorer is None:
            # Lazy import prevents model loading during health checks,
            # unit tests, and import-time startup.
            from .inference import ScamRiskScorer

            self._scorer = ScamRiskScorer()

        return self._scorer

    def analyze_message(self, message: str) -> dict[str, Any]:
        text = self._validate_message(message)

        signal_obj = self.scorer.analyze(text)
        if hasattr(signal_obj, "to_dict"):
            ml_signal = signal_obj.to_dict()
        else:
            ml_signal = asdict(signal_obj)

        evidence, protective = detect_evidence(text)

        decision = decide_risk(
            ml_signal=ml_signal,
            evidence=evidence,
            protective_evidence=protective,
        )

        exhibit = build_exhibit(decision, text)

        return {
            "verdict": decision["verdict"],
            "ml_signal": decision["ml_signal"],
            "evidence": decision["evidence"],
            "protective_evidence": decision["protective_evidence"],
            "reason_codes": decision["reason_codes"],
            "exhibit": exhibit,
            "meta": {
                "message_length": len(text),
                "evidence_count": len(decision["evidence"]),
                "protective_evidence_count": len(
                    decision["protective_evidence"]
                ),
            },
        }

    @staticmethod
    def _validate_message(message: str) -> str:
        if not isinstance(message, str):
            raise AnalysisValidationError(
                "message must be a string"
            )

        text = message.strip()

        if not text:
            raise AnalysisValidationError(
                "message must not be empty"
            )

        if len(text) > MAX_MESSAGE_LENGTH:
            raise AnalysisValidationError(
                f"message must be at most {MAX_MESSAGE_LENGTH} characters"
            )

        return text


_default_service: ScamAnalysisService | None = None


def get_analysis_service() -> ScamAnalysisService:
    global _default_service

    if _default_service is None:
        _default_service = ScamAnalysisService()

    return _default_service


def analyze_message(message: str) -> dict[str, Any]:
    return get_analysis_service().analyze_message(message)
