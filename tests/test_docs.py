from dataclasses import dataclass

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


def make_client():
    app = create_app(
        ScamAnalysisService(scorer=FakeScorer())
    )
    return TestClient(app)


def test_swagger_docs_are_enabled():
    response = make_client().get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Swagger UI" in response.text


def test_openapi_schema_is_enabled():
    response = make_client().get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "Scam Museum API"
    assert schema["info"]["version"] == "0.1.0"
    assert "/health" in schema["paths"]
    assert "/api/analyze" in schema["paths"]


def test_frontend_root_stays_out_of_api_schema():
    schema = make_client().get("/openapi.json").json()

    assert "/" not in schema["paths"]


def test_redoc_stays_disabled():
    response = make_client().get("/redoc")

    assert response.status_code == 404
