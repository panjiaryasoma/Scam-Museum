from pathlib import Path

import pytest


MODEL = Path("models/scam_classifier_v05.joblib")
METADATA = Path("models/scam_classifier_v05_metadata.json")
NORMALIZER = Path("ml/v02_text.py")


@pytest.mark.integration
def test_actual_v05_hybrid_pipeline():
    if not (MODEL.exists() and METADATA.exists() and NORMALIZER.exists()):
        pytest.skip("Frozen v0.5 local model artifacts are not available.")

    # Import only after local artifacts are confirmed, so this test can be
    # collected safely in environments that only contain the core kit.
    from app.core.evidence import detect_evidence
    from app.core.exhibit import build_exhibit
    from app.core.inference import ScamRiskScorer
    from app.core.risk import decide_risk

    text = (
        "Your account will be suspended immediately. "
        "Send us your OTP to verify your account."
    )

    scorer = ScamRiskScorer(MODEL, METADATA)
    ml_signal = scorer.analyze(text).to_dict()
    evidence, protective = detect_evidence(text)
    analysis = decide_risk(ml_signal, evidence, protective)
    exhibit = build_exhibit(analysis, text)

    assert ml_signal["model_version"] == "0.5"
    assert ml_signal["label"] in {"WEAK", "ELEVATED", "STRONG"}
    assert analysis["verdict"] == "HIGH RISK"
    assert exhibit["verdict"] == "HIGH RISK"
