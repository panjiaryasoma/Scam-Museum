from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from app.core.service import (
    AnalysisValidationError,
    ScamAnalysisService,
    get_analysis_service,
)


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
TEMPLATE_DIR = APP_DIR / "templates"


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    message: str


def create_app(
    analysis_service: ScamAnalysisService | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Scam Museum API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    app.state.analysis_service = analysis_service

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

    def current_service() -> ScamAnalysisService:
        injected = app.state.analysis_service
        if injected is not None:
            return injected
        return get_analysis_service()

    @app.get("/", include_in_schema=False)
    async def museum_home() -> FileResponse:
        return FileResponse(
            TEMPLATE_DIR / "index.html",
            media_type="text/html",
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "scam-museum",
            "api_version": "0.1",
        }

    @app.post("/api/analyze")
    async def analyze(payload: AnalyzeRequest) -> JSONResponse:
        try:
            result = current_service().analyze_message(payload.message)
        except AnalysisValidationError as exc:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_MESSAGE",
                        "message": str(exc),
                    }
                },
            )
        except FileNotFoundError:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "MODEL_UNAVAILABLE",
                        "message": (
                            "The frozen ML model artifact is unavailable."
                        ),
                    }
                },
            )
        except Exception:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "ANALYSIS_FAILED",
                        "message": (
                            "The message could not be analyzed."
                        ),
                    }
                },
            )

        return JSONResponse(
            status_code=200,
            content=result,
        )

    return app


app = create_app()
