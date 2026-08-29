from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib

from ml.v02_text import normalize_model_text


@dataclass(frozen=True)
class MLSignal:
    label: str
    score: float
    model_version: str
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScamRiskScorer:
    """Use frozen v0.5 only as a text-risk signal."""

    def __init__(
        self,
        model_path: str | Path = "models/scam_classifier_v05.joblib",
        metadata_path: str | Path = "models/scam_classifier_v05_metadata.json",
    ) -> None:
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)

        self.model = joblib.load(self.model_path)
        self.metadata = json.loads(
            self.metadata_path.read_text(encoding="utf-8")
        )
        self.threshold = float(self.metadata.get("threshold", 0.80))
        self.version = str(self.metadata.get("version", "0.5"))

    def _score(self, normalized_text: str) -> float:
        if hasattr(self.model, "predict_proba"):
            return float(self.model.predict_proba([normalized_text])[0, 1])

        raw = float(self.model.decision_function([normalized_text])[0])
        return 1.0 / (1.0 + math.exp(-raw))

    def analyze(self, text: str) -> MLSignal:
        normalized = normalize_model_text(text)
        score = self._score(normalized)

        if score >= self.threshold:
            label = "STRONG"
        elif score >= 0.50:
            label = "ELEVATED"
        else:
            label = "WEAK"

        return MLSignal(
            label=label,
            score=score,
            model_version=self.version,
            threshold=self.threshold,
        )
