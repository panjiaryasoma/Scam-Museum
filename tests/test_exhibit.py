from app.core.evidence import detect_evidence
from app.core.exhibit import build_exhibit
from app.core.risk import decide_risk


def exhibit_for(text, ml_label="WEAK"):
    evidence, protective = detect_evidence(text)
    analysis = decide_risk(
        {
            "label": ml_label,
            "score": 0.85 if ml_label == "STRONG" else 0.10,
            "model_version": "test",
            "threshold": 0.80,
        },
        evidence,
        protective,
    )
    return build_exhibit(analysis, text)


def test_urgency_trap_title():
    exhibit = exhibit_for(
        "Your account is locked. Verify immediately at "
        "https://bit.ly/example"
    )
    assert exhibit["title"] == "THE URGENCY TRAP"


def test_incomplete_artifact_title():
    assert exhibit_for("Hi, is this Sarah?")["title"] == "AN INCOMPLETE ARTIFACT"


def test_plain_message_title():
    assert (
        exhibit_for("Dinner is at seven. See you at home.")["title"]
        == "NO CLEAR DECEPTION PATTERN"
    )


def test_original_message_is_preserved():
    text = "Please send £900 today."
    assert exhibit_for(text)["artifact_text"] == text
