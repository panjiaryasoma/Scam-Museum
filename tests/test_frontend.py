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
    app = create_app(ScamAnalysisService(scorer=FakeScorer()))
    return TestClient(app)


def test_home_renders_museum(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SCAM MUSEUM" in response.text
    assert "Every scam leaves artifacts." in response.text
    assert "Gallery of Digital Deception" in response.text
    assert 'id="collection"' in response.text
    assert 'id="exhibit-grid"' in response.text
    assert 'id="exhibit-dialog"' in response.text
    assert 'id="message-input"' in response.text
    assert 'id="result-section"' in response.text
    assert 'id="view-similar-exhibits"' in response.text


def test_home_keeps_visitor_analysis_private_by_default(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Private visitor analyses are never automatically added to the collection." in response.text
    assert "Visitor analyses are not automatically published to the museum collection." in response.text


def test_home_exposes_gallery_filter_controls(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'data-gallery-filter="all"' in response.text
    assert 'data-gallery-filter="banking"' in response.text
    assert 'data-gallery-filter="job"' in response.text


def test_css_is_served(client):
    response = client.get("/static/css/app.css")

    assert response.status_code == 200
    assert "--museum" in response.text
    assert ".artifact-frame" in response.text


def test_museum_css_is_served(client):
    response = client.get("/static/css/museum.css")

    assert response.status_code == 200
    assert "--gallery-brass" in response.text
    assert ".museum-hero" in response.text
    assert ".exhibit-grid" in response.text
    assert ".exhibit-dialog" in response.text


def test_mobile_css_is_served_and_scoped(client):
    response = client.get("/static/css/mobile.css")

    assert response.status_code == 200
    assert "@media (max-width: 820px)" in response.text
    assert "@media (max-width: 520px)" in response.text
    assert ".collection-filters" in response.text
    assert ".exhibit-dialog" in response.text


def test_javascript_is_served(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert 'fetch("/api/analyze"' in response.text
    assert "renderHighlightedText" in response.text
    assert "scam-museum:analysis-rendered" in response.text
    assert 'link.href = "/static/css/mobile.css"' in response.text
    assert 'link.media = "(max-width: 820px)"' in response.text


def test_gallery_javascript_is_served(client):
    response = client.get("/static/js/gallery.js")

    assert response.status_code == 200
    assert "The Urgency Trap" in response.text
    assert "Reconstructed demonstration" in response.text
    assert 'querySelectorAll("[data-gallery-filter]")' in response.text
    assert "scam-museum:analysis-rendered" in response.text


def test_frontend_has_no_duplicate_verdict_logic(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    source = response.text

    # The frontend may display verdict values, but it must not contain
    # evidence-to-verdict decision rules.
    assert "CRITICAL_REQUEST_WITH_SUPPORTING_EVIDENCE" not in source
    assert "MULTIPLE_CRITICAL_REQUESTS" not in source
