from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def runtime_requirements():
    text = (ROOT / "requirements.txt").read_text(
        encoding="utf-8"
    )
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_pyproject_and_requirements_share_runtime_dependencies():
    pyproject = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    dependencies = pyproject["project"]["dependencies"]

    assert dependencies == runtime_requirements()


def test_python_runtime_is_locked_to_312():
    pyproject = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    assert (
        pyproject["project"]["requires-python"]
        == ">=3.12,<3.13"
    )
    assert "tool" not in pyproject or "vercel" not in pyproject.get("tool", {})

    assert (
        (ROOT / ".python-version")
        .read_text(encoding="utf-8")
        .strip()
        == "3.12"
    )


def test_vercel_uses_zero_config_root_fastapi_entrypoint():
    assert not (ROOT / "vercel.json").exists()
    assert not (ROOT / "api" / "index.py").exists()

    entrypoint = (ROOT / "main.py").read_text(
        encoding="utf-8"
    )

    assert "from app.main import app" in entrypoint
    assert '__all__ = ["app"]' in entrypoint


def test_vercel_bundle_keeps_active_runtime_artifacts():
    ignored = (ROOT / ".vercelignore").read_text(
        encoding="utf-8"
    )

    assert "tests/" in ignored
    assert "reports/" in ignored
    assert "data/" in ignored
    assert "scripts/" in ignored

    assert "models/scam_classifier_v04.joblib" in ignored
    assert "models/scam_classifier_v04_metadata.json" in ignored

    assert "models/scam_classifier_v05.joblib" not in ignored
    assert "models/scam_classifier_v05_metadata.json" not in ignored
    assert "app/" not in ignored
    assert "ml/" not in ignored
    assert "main.py" not in ignored
