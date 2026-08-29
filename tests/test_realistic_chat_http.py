from __future__ import annotations
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core.service import ScamAnalysisService
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/realistic_chat_cases.json"
MODEL = ROOT / "models/scam_classifier_v05.joblib"
META = ROOT / "models/scam_classifier_v05_metadata.json"
ALLOWED = {"HIGH RISK","SUSPICIOUS","LOW RISK","INSUFFICIENT EVIDENCE"}

CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]

@pytest.fixture(scope="module")
def client():
    if not MODEL.exists() or not META.exists():
        pytest.skip("Frozen v0.5 model artifacts unavailable.")
    app = create_app(analysis_service=ScamAnalysisService())
    with TestClient(app) as c:
        yield c

@pytest.mark.integration
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_realistic_chat_survives_full_http_pipeline(client, case):
    r = client.post("/api/analyze", json={"message": case["message"]})
    assert r.status_code == 200
    out = r.json()
    assert out["verdict"] in ALLOWED
    assert out["exhibit"]["verdict"] == out["verdict"]
    assert out["exhibit"]["artifact_text"] == case["message"]
    assert out["meta"]["message_length"] == len(case["message"])
    for item in out["evidence"] + out["protective_evidence"]:
        if "start" in item and "end" in item:
            assert 0 <= item["start"] < item["end"] <= len(case["message"])
            assert case["message"][item["start"]:item["end"]] == item["matched_text"]
