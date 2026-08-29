from __future__ import annotations

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_requirements_are_locked():
    text = (ROOT / "requirements.txt").read_text(
        encoding="utf-8"
    )

    required = {
        "fastapi==0.141.1",
        "scikit-learn==1.9.0",
        "numpy==2.3.2",
        "scipy==1.17.0",
        "joblib==1.5.3",
    }

    lines = {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    }

    assert required == lines
    assert "uvicorn" not in text
    assert "httpx" not in text
    assert "pytest" not in text


def test_local_app_requirements_extend_production():
    text = (ROOT / "requirements-app.txt").read_text(
        encoding="utf-8"
    )

    assert "-r requirements.txt" in text
    assert "uvicorn==0.41.0" in text
    assert "httpx>=0.27,<1.0" in text


def test_python_runtime_is_locked_to_312():
    pyproject = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    project = pyproject["project"]

    assert project["requires-python"] == ">=3.12,<3.13"
    assert (
        pyproject["tool"]["vercel"]["entrypoint"]
        == "app.main:app"
    )

    assert (
        ROOT.joinpath(".python-version")
        .read_text(encoding="utf-8")
        .strip()
        == "3.12"
    )


def test_vercel_bundle_keeps_runtime_and_excludes_old_artifacts():
    config = json.loads(
        (ROOT / "vercel.json").read_text(
            encoding="utf-8"
        )
    )

    function = config["functions"]["app/main.py"]
    excluded = function["excludeFiles"]

    assert "tests/**" in excluded
    assert "data/**" in excluded
    assert "reports/**" in excluded
    assert "scam_classifier_v04.joblib" in excluded

    # The active production artifacts must not be excluded.
    assert "scam_classifier_v05.joblib" not in excluded
    assert "scam_classifier_v05_metadata.json" not in excluded

    # Runtime code/assets must remain available to the FastAPI app.
    assert "app/**" not in excluded
    assert "ml/**" not in excluded
    assert "models/**" not in excluded
