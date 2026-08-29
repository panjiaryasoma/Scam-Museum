from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.service import ScamAnalysisService
from app.main import create_app


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "message_cases.json"
MODEL_PATH = ROOT / "models" / "scam_classifier_v05.joblib"
METADATA_PATH = ROOT / "models" / "scam_classifier_v05_metadata.json"

# Small browser-facing acceptance subset.
# These cases already exist in the locked message fixture corpus, so the
# expected behavior is not duplicated in a second source of truth.
MANUAL_CASE_IDS = [
    "H01",  # OTP phishing
    "H05",  # shortened URL + account threat
    "H06",  # family impersonation + money transfer
    "S01",  # bare OTP request
    "L01",  # legitimate protective OTP
    "L03",  # ordinary conversation
    "L04",  # normal non-shortened URL
    "I01",  # wrong-number opener
    "I02",  # family/new-number opener without request
]


def _load_manual_cases():
    payload = json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )
    by_id = {
        case["id"]: case
        for case in payload["cases"]
    }
    return [by_id[case_id] for case_id in MANUAL_CASE_IDS]


MANUAL_CASES = _load_manual_cases()


@pytest.fixture(scope="module")
def manual_client():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        pytest.skip(
            "Frozen v0.5 model artifacts are not available."
        )

    service = ScamAnalysisService()
    app = create_app(analysis_service=service)

    with TestClient(app) as client:
        yield client


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    MANUAL_CASES,
    ids=[case["id"] for case in MANUAL_CASES],
)
def test_manual_text_submission_through_http(
    manual_client,
    case,
):
    response = manual_client.post(
        "/api/analyze",
        json={"message": case["message"]},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["verdict"] == case["expected_verdict"]
    assert result["exhibit"]["verdict"] == case["expected_verdict"]
    assert result["exhibit"]["artifact_text"] == case["message"]

    assert "ml_signal" in result
    assert isinstance(result["evidence"], list)
    assert isinstance(result["protective_evidence"], list)
    assert result["meta"]["message_length"] == len(case["message"])


def test_manual_text_submission_rejects_blank_message(
    manual_client,
):
    response = manual_client.post(
        "/api/analyze",
        json={"message": "   "},
    )

    assert response.status_code == 422

    result = response.json()

    assert result["error"]["code"] == "INVALID_MESSAGE"


def test_manual_text_submission_rejects_oversized_message(
    manual_client,
):
    response = manual_client.post(
        "/api/analyze",
        json={"message": "A" * 5001},
    )

    assert response.status_code == 422

    result = response.json()

    assert result["error"]["code"] == "INVALID_MESSAGE"
