from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.core.service import ScamAnalysisService
from app.main import create_app


@dataclass(frozen=True)
class FakeSignal:
    label: str = "WEAK"
    score: float = 0.10
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


@pytest.fixture()
def client():
    app = create_app(
        ScamAnalysisService(scorer=FakeScorer())
    )
    return TestClient(app)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["service"] == "scam-museum"


def test_analyze_success(client):
    response = client.post(
        "/api/analyze",
        json={
            "message": (
                "Your account will be suspended immediately. "
                "Send us your OTP to verify your account."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["verdict"] == "HIGH RISK"
    assert (
        body["exhibit"]["title"]
        == "THE VERIFICATION TRAP"
    )
    assert body["ml_signal"]["model_version"] == "test"


def test_analyze_requires_message(client):
    response = client.post("/api/analyze", json={})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "message",
    ["", "   "],
)
def test_analyze_rejects_empty_message(
    client,
    message,
):
    response = client.post(
        "/api/analyze",
        json={"message": message},
    )

    assert response.status_code == 422
    assert (
        response.json()["error"]["code"]
        == "INVALID_MESSAGE"
    )


def test_analyze_rejects_non_string_message(client):
    response = client.post(
        "/api/analyze",
        json={"message": 123},
    )

    assert response.status_code == 422


def test_analyze_rejects_non_json_body(client):
    response = client.post(
        "/api/analyze",
        content="hello",
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 422
