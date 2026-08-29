const OCR_SCRIPT_URL = "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js";
const ACCEPTED_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const MAX_TEXT_LENGTH = 5000;

const input = document.getElementById("message-input");
const analyzeButton = document.getElementById("analyze-button");

let tesseractPromise = null;
let activePreviewUrl = null;

function loadStylesheet() {
  if (document.querySelector('link[data-ocr-styles="true"]')) {
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = "/static/css/ocr.css";
  link.dataset.ocrStyles = "true";
  document.head.append(link);
}

function loadTesseract() {
  if (window.Tesseract) {
    return Promise.resolve(window.Tesseract);
  }

  if (tesseractPromise) {
    return tesseractPromise;
  }

  tesseractPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = OCR_SCRIPT_URL;
    script.async = true;
    script.crossOrigin = "anonymous";
    script.onload = () => {
      if (window.Tesseract) {
        resolve(window.Tesseract);
        return;
      }
      reject(new Error("OCR library loaded without exposing Tesseract."));
    };
    script.onerror = () => reject(new Error("OCR library could not be loaded."));
    document.head.append(script);
  });

  return tesseractPromise;
}

function cleanExtractedText(value) {
  return String(value || "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function percentageFromProgress(message) {
  if (typeof message?.progress !== "number") {
    return null;
  }
  return Math.max(0, Math.min(100, Math.round(message.progress * 100)));
}

function clipboardImageFile(event) {
  const files = Array.from(event.clipboardData?.files || []);
  const directFile = files.find((file) => ACCEPTED_TYPES.has(file.type));

  if (directFile) {
    return directFile;
  }

  const items = Array.from(event.clipboardData?.items || []);
  const imageItem = items.find(
    (item) => item.kind === "file" && ACCEPTED_TYPES.has(item.type)
  );

  return imageItem?.getAsFile?.() || null;
}

function createAdapter() {
  if (!input || document.getElementById("ocr-adapter")) {
    return null;
  }

  const adapter = document.createElement("section");
  adapter.id = "ocr-adapter";
  adapter.className = "ocr-adapter";
  adapter.setAttribute("aria-label", "Screenshot text extraction");

  const controls = document.createElement("div");
  controls.className = "ocr-controls";

  const fileInput = document.createElement("input");
  fileInput.id = "screenshot-input";
  fileInput.className = "sr-only";
  fileInput.type = "file";
  fileInput.accept = "image/png,image/jpeg,image/webp";

  const uploadButton = document.createElement("button");
  uploadButton.id = "screenshot-upload-button";
  uploadButton.className = "button-secondary ocr-upload-button";
  uploadButton.type = "button";
  uploadButton.textContent = "Upload screenshot";

  const copy = document.createElement("div");
  copy.className = "ocr-copy";

  const label = document.createElement("strong");
  label.textContent = "Extract text from an image";

  const helper = document.createElement("span");
  helper.className = "caption";
  helper.textContent = "Upload PNG, JPG, or WebP up to 8 MB, or paste a screenshot into the message box with Ctrl+V. Review extracted text before analysis.";

  copy.append(label, helper);
  controls.append(fileInput, uploadButton, copy);

  const feedback = document.createElement("div");
  feedback.className = "ocr-feedback";

  const preview = document.createElement("img");
  preview.id = "ocr-preview";
  preview.className = "ocr-preview";
  preview.alt = "Selected screenshot preview";
  preview.hidden = true;

  const status = document.createElement("p");
  status.id = "ocr-status";
  status.className = "ocr-status caption";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  status.textContent = "Image stays in your browser. OCR does not run the scam classifier.";

  feedback.append(preview, status);
  adapter.append(controls, feedback);

  input.parentNode.insertBefore(adapter, input);

  uploadButton.addEventListener("click", () => {
    if (!uploadButton.disabled) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      return;
    }

    await processScreenshot({ file, uploadButton, fileInput, preview, status, adapter });
  });

  input.addEventListener("paste", async (event) => {
    const file = clipboardImageFile(event);

    if (!file) {
      return;
    }

    event.preventDefault();
    setStatus(status, "Screenshot pasted. Preparing OCR…");
    await processScreenshot({ file, uploadButton, fileInput, preview, status, adapter });
  });

  return adapter;
}

function setBusy({ busy, uploadButton, fileInput, adapter }) {
  uploadButton.disabled = busy;
  fileInput.disabled = busy;
  adapter.setAttribute("aria-busy", busy ? "true" : "false");

  if (analyzeButton) {
    analyzeButton.disabled = busy;
  }
}

function setStatus(status, message, state = "neutral") {
  status.textContent = message;
  status.dataset.state = state;
}

function showPreview(preview, file) {
  if (activePreviewUrl) {
    URL.revokeObjectURL(activePreviewUrl);
  }

  activePreviewUrl = URL.createObjectURL(file);
  preview.src = activePreviewUrl;
  preview.hidden = false;
}

function validateFile(file) {
  if (!ACCEPTED_TYPES.has(file.type)) {
    throw new Error("Use a PNG, JPG, or WebP screenshot.");
  }

  if (file.size > MAX_FILE_BYTES) {
    throw new Error("Screenshot is larger than 8 MB.");
  }
}

async function processScreenshot({ file, uploadButton, fileInput, preview, status, adapter }) {
  try {
    validateFile(file);
    showPreview(preview, file);
    setBusy({ busy: true, uploadButton, fileInput, adapter });
    uploadButton.textContent = "Extracting text…";
    setStatus(status, `Preparing OCR for ${file.name || "pasted screenshot"}…`);

    const Tesseract = await loadTesseract();
    const result = await Tesseract.recognize(file, "eng", {
      logger(message) {
        const progress = percentageFromProgress(message);
        const phase = message?.status ? String(message.status) : "processing image";
        setStatus(
          status,
          progress === null
            ? `${phase}…`
            : `${phase} · ${progress}%`
        );
      },
    });

    const extracted = cleanExtractedText(result?.data?.text);

    if (!extracted) {
      throw new Error("No readable text was found in this screenshot.");
    }

    const trimmed = extracted.slice(0, MAX_TEXT_LENGTH);
    input.value = trimmed;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.focus();

    if (extracted.length > MAX_TEXT_LENGTH) {
      setStatus(
        status,
        "OCR complete. Text was trimmed to 5000 characters; review it before analysis.",
        "warning"
      );
    } else {
      setStatus(
        status,
        "OCR complete. Review the extracted text, correct any mistakes, then analyze it.",
        "success"
      );
    }
  } catch (error) {
    setStatus(
      status,
      error instanceof Error ? error.message : "Screenshot text extraction failed.",
      "error"
    );
  } finally {
    setBusy({ busy: false, uploadButton, fileInput, adapter });
    uploadButton.textContent = "Upload another screenshot";
    fileInput.value = "";
  }
}

loadStylesheet();
createAdapter();
