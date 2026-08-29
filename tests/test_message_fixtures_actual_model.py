from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.service import ScamAnalysisService


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "message_cases.json"
)

MODEL_PATH = Path("models/scam_classifier_v05.joblib")
METADATA_PATH = Path(
    "models/scam_classifier_v05_metadata.json"
)


def load_smoke_cases():
    payload = json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )
    return [
        case
        for case in payload["cases"]
        if case.get("actual_model_smoke")
    ]


SMOKE_CASES = load_smoke_cases()


@pytest.fixture(scope="module")
def actual_service():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        pytest.skip(
            "Frozen v0.5 model artifacts are not available."
        )

    return ScamAnalysisService()


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    SMOKE_CASES,
    ids=[case["id"] for case in SMOKE_CASES],
)
def test_actual_v05_message_fixtures(
    actual_service,
    case,
):
    result = actual_service.analyze_message(
        case["message"]
    )

    assert result["verdict"] == case["expected_verdict"]
