from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.core.service import ScamAnalysisService


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "message_cases.json"
)


@dataclass(frozen=True)
class FixtureSignal:
    label: str
    score: float
    model_version: str = "fixture"
    threshold: float = 0.80

    def to_dict(self):
        return {
            "label": self.label,
            "score": self.score,
            "model_version": self.model_version,
            "threshold": self.threshold,
        }


class FixtureScorer:
    def __init__(self, label: str):
        self.label = label

    def analyze(self, text: str):
        scores = {
            "WEAK": 0.10,
            "ELEVATED": 0.65,
            "STRONG": 0.85,
        }
        return FixtureSignal(
            label=self.label,
            score=scores[self.label],
        )


def load_cases():
    payload = json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )
    return payload["cases"]


CASES = load_cases()


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[case["id"] for case in CASES],
)
def test_message_fixture_contract(case):
    service = ScamAnalysisService(
        scorer=FixtureScorer(case["ml_label"])
    )

    result = service.analyze_message(case["message"])

    assert result["verdict"] == case["expected_verdict"]

    evidence_ids = {
        item["id"] for item in result["evidence"]
    }
    protective_ids = {
        item["id"]
        for item in result["protective_evidence"]
    }

    for expected in case.get(
        "expected_evidence", []
    ):
        assert expected in evidence_ids

    for expected in case.get(
        "expected_protective_evidence", []
    ):
        assert expected in protective_ids

    for forbidden in case.get(
        "forbidden_evidence", []
    ):
        assert forbidden not in evidence_ids

    assert result["exhibit"]["verdict"] == case["expected_verdict"]
    assert result["exhibit"]["artifact_text"] == case["message"]
