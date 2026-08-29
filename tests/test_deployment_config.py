from __future__ import annotations

import json
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


def test_vercel_uses_documented_api_index_entrypoint():
    config = json.loads(
        (ROOT / "vercel.json").read_text(
            encoding="utf-8"
        )
    )

    assert "api/index.py" in config["functions"]
    assert "app/main.py" not in config["functions"]

    assert config["rewrites"] == [
        {
            "source": "/(.*)",
            "destination": "/api/index.py",
        }
    ]


def test_vercel_bundle_keeps_active_runtime_artifacts():
    config = json.loads(
        (ROOT / "vercel.json").read_text(
            encoding="utf-8"
        )
    )

    excluded = (
        config["functions"]["api/index.py"]
        ["excludeFiles"]
    )

    assert "tests/**" in excluded
    assert "reports/**" in excluded
    assert "data/**" in excluded
    assert "scripts/**" in excluded

    assert "scam_classifier_v04.joblib" in excluded

    assert "scam_classifier_v05.joblib" not in excluded
    assert "scam_classifier_v05_metadata.json" not in excluded
    assert "app/**" not in excluded
    assert "ml/**" not in excluded
