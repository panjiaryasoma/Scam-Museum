from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "app" / "static" / "js" / "app.js"
OCR_JS = ROOT / "app" / "static" / "js" / "ocr.js"
OCR_CSS = ROOT / "app" / "static" / "css" / "ocr.css"
INDEX_HTML = ROOT / "app" / "templates" / "index.html"
SHARE_JS = ROOT / "app" / "static" / "js" / "share-card.js"


def test_core_frontend_progressively_loads_ocr_adapter():
    source = APP_JS.read_text(encoding="utf-8")

    assert 'import("/static/js/ocr.js")' in source
    assert "Screenshot OCR adapter could not be loaded." in source


def test_ocr_adapter_is_input_only_and_does_not_run_classifier():
    source = OCR_JS.read_text(encoding="utf-8")

    assert 'document.getElementById("message-input")' in source
    assert 'input.dispatchEvent(new Event("input"' in source
    assert 'fetch("/api/analyze"' not in source
    assert "analyzeMessage(" not in source


def test_ocr_adapter_restricts_image_types_and_size():
    source = OCR_JS.read_text(encoding="utf-8")

    assert '"image/png"' in source
    assert '"image/jpeg"' in source
    assert '"image/webp"' in source
    assert "8 * 1024 * 1024" in source
    assert "MAX_TEXT_LENGTH = 5000" in source


def test_ocr_adapter_requires_review_before_analysis():
    source = OCR_JS.read_text(encoding="utf-8")

    assert "Review the extracted text" in source
    assert "OCR does not run the scam classifier." in source


def test_ocr_styles_preserve_square_museum_controls():
    source = OCR_CSS.read_text(encoding="utf-8")

    assert ".ocr-adapter" in source
    assert ".ocr-upload-button" in source
    assert "border-radius" not in source


def test_message_input_accepts_pasted_screenshot_without_hijacking_text_paste():
    source = OCR_JS.read_text(encoding="utf-8")

    assert 'input.addEventListener("paste"' in source
    assert "clipboardImageFile(event)" in source
    assert "event.preventDefault()" in source
    assert "if (!file)" in source


def test_ocr_branch_preserves_share_exhibit_feature():
    html = INDEX_HTML.read_text(encoding="utf-8")
    share_source = SHARE_JS.read_text(encoding="utf-8")

    assert 'id="share-exhibit"' in html
    assert '/static/css/share-card.css' in html
    assert '/static/js/share-card.js' in html
    assert "navigator.share" in share_source
    assert 'fetch("/api/analyze"' not in share_source
