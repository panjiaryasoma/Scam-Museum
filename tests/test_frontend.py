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


def test_home_renders_museum(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SCAM MUSEUM" in response.text
    assert "Every scam leaves artifacts." in response.text
    assert 'id="message-input"' in response.text
    assert 'id="result-section"' in response.text


def test_css_is_served(client):
    response = client.get("/static/css/app.css")

    assert response.status_code == 200
    assert "--museum" in response.text
    assert ".artifact-frame" in response.text


def test_javascript_is_served(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'fetch("/api/analyze"' in response.text
    assert "renderHighlightedText" in response.text


def test_frontend_has_no_duplicate_verdict_logic(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    source = response.text

    # The frontend may display verdict values, but it must not contain
    # evidence-to-verdict decision rules.
    assert "CRITICAL_REQUEST_WITH_SUPPORTING_EVIDENCE" not in source
    assert "MULTIPLE_CRITICAL_REQUESTS" not in source
