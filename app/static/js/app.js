const input = document.getElementById("message-input");
const analyzeButton = document.getElementById("analyze-button");
const characterCount = document.getElementById("character-count");
const formError = document.getElementById("form-error");
const resultSection = document.getElementById("result-section");
const loadingOverlay = document.getElementById("loading-overlay");
const analyzeAnother = document.getElementById("analyze-another");

const exhibitTitle = document.getElementById("exhibit-title");
const verdictPlaque = document.getElementById("verdict-plaque");
const verdictText = document.getElementById("verdict-text");
const mlSignal = document.getElementById("ml-signal");
const highlightedMessage = document.getElementById("highlighted-message");
const evidenceList = document.getElementById("evidence-list");
const protectiveBlock = document.getElementById("protective-block");
const protectiveList = document.getElementById("protective-list");
const curatorialNote = document.getElementById("curatorial-note");
const warningNote = document.querySelector(".warning-note");

const EVIDENCE_LABELS = {
  OTP_REQUEST: "OTP request",
  CREDENTIAL_REQUEST: "Credential request",
  FINANCIAL_INFO_REQUEST: "Financial information request",
  GIFT_CARD_REQUEST: "Gift card request",
  RISKY_ATTACHMENT: "Risky attachment",
  MONEY_TRANSFER_REQUEST: "Money transfer request",
  PAYMENT_REQUEST: "Payment request",
  SUSPICIOUS_URL: "Suspicious URL",
  REPLY_OR_CALL_REQUEST: "Reply or call request",
  TIME_URGENCY: "Time urgency",
  ACCOUNT_THREAT: "Account threat",
  AUTHORITY_CLAIM: "Authority claim",
  RECOVERY_LURE: "Recovery lure",
  NEED_AND_GREED: "Reward or benefit lure",
  FAMILY_IMPERSONATION: "Family impersonation",
  NEW_NUMBER_CLAIM: "New number claim",
  UNEXPECTED_CONTACT: "Unexpected contact",
  PROTECTIVE_DO_NOT_SHARE: "Do-not-share warning",
  ANTI_SCAM_ADVICE: "Anti-scam advice",
};

const VERDICT_NOTES = {
  "HIGH RISK": {
    text: "↳ Please do not interact with the exhibit.",
    color: "#fca5a5",
  },
  SUSPICIOUS: {
    text: "↳ Verify before interacting.",
    color: "#fde047",
  },
  "INSUFFICIENT EVIDENCE": {
    text: "↳ More context required.",
    color: "var(--text-tertiary)",
  },
  "LOW RISK": {
    text: "↳ No material deception pattern observed.",
    color: "#bef264",
  },
};

function updateCharacterCount() {
  characterCount.textContent = `${input.value.length} / 5000`;
}

function setLoading(isLoading) {
  loadingOverlay.hidden = !isLoading;
  analyzeButton.disabled = isLoading;
}

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function clearError() {
  formError.textContent = "";
  formError.hidden = true;
}

function labelFor(id) {
  return EVIDENCE_LABELS[id] || id.replaceAll("_", " ").toLowerCase();
}

function mergeHighlightRanges(items, textLength) {
  const ranges = items
    .filter((item) => Number.isInteger(item.start) && Number.isInteger(item.end))
    .map((item) => ({
      start: Math.max(0, Math.min(item.start, textLength)),
      end: Math.max(0, Math.min(item.end, textLength)),
    }))
    .filter((item) => item.end > item.start)
    .sort((a, b) => a.start - b.start || a.end - b.end);

  const merged = [];

  for (const range of ranges) {
    const last = merged[merged.length - 1];

    if (!last || range.start > last.end) {
      merged.push({ ...range });
      continue;
    }

    last.end = Math.max(last.end, range.end);
  }

  return merged;
}

function renderHighlightedText(text, evidence) {
  highlightedMessage.replaceChildren();
  const ranges = mergeHighlightRanges(evidence, text.length);

  if (!ranges.length) {
    highlightedMessage.append(document.createTextNode(text));
    return;
  }

  let cursor = 0;

  for (const range of ranges) {
    if (range.start > cursor) {
      highlightedMessage.append(
        document.createTextNode(text.slice(cursor, range.start))
      );
    }

    const mark = document.createElement("mark");
    mark.textContent = text.slice(range.start, range.end);
    highlightedMessage.append(mark);
    cursor = range.end;
  }

  if (cursor < text.length) {
    highlightedMessage.append(document.createTextNode(text.slice(cursor)));
  }
}

function makeFindingItem(item, index) {
  const row = document.createElement("div");
  row.className = "finding-item";

  const number = document.createElement("span");
  number.className = "finding-index";
  number.textContent = String(index + 1).padStart(2, "0");

  const content = document.createElement("div");

  const title = document.createElement("strong");
  title.textContent = labelFor(item.id);

  const rationale = document.createElement("p");
  rationale.textContent = item.rationale || "Observable message pattern.";

  content.append(title, rationale);
  row.append(number, content);

  return row;
}

function uniqueFindingsById(items) {
  const seen = new Set();

  return items.filter((item) => {
    if (!item?.id || seen.has(item.id)) {
      return false;
    }

    seen.add(item.id);
    return true;
  });
}

function renderEvidence(items) {
  evidenceList.replaceChildren();
  const uniqueItems = uniqueFindingsById(items);

  if (!uniqueItems.length) {
    const empty = document.createElement("p");
    empty.className = "finding-empty";
    empty.textContent = "No material observable risk artifacts were cataloged.";
    evidenceList.append(empty);
    return;
  }

  uniqueItems.forEach((item, index) => {
    evidenceList.append(makeFindingItem(item, index));
  });
}

function renderProtective(items) {
  protectiveList.replaceChildren();
  const uniqueItems = uniqueFindingsById(items);

  if (!uniqueItems.length) {
    protectiveBlock.hidden = true;
    return;
  }

  protectiveBlock.hidden = false;

  uniqueItems.forEach((item, index) => {
    protectiveList.append(makeFindingItem(item, index));
  });
}

function renderVerdictNote(verdict) {
  if (!warningNote) {
    return;
  }

  const note = VERDICT_NOTES[verdict] || {
    text: "↳ Review the result before acting.",
    color: "var(--text-tertiary)",
  };

  warningNote.textContent = note.text;
  warningNote.style.color = note.color;
}

function renderResult(data) {
  const exhibit = data.exhibit || {};
  const verdict = data.verdict || "";

  exhibitTitle.textContent = exhibit.title || "Unclassified artifact";
  verdictText.textContent = verdict || "—";
  verdictPlaque.dataset.verdict = verdict;
  renderVerdictNote(verdict);

  const signalLabel = data.ml_signal?.label || "—";
  mlSignal.textContent = `ML risk signal: ${signalLabel}`;

  const artifactText = exhibit.artifact_text || input.value.trim();

  renderHighlightedText(artifactText, data.evidence || []);
  renderEvidence(data.evidence || []);
  renderProtective(data.protective_evidence || []);

  curatorialNote.textContent =
    exhibit.curatorial_note || "No curatorial note was returned.";

  resultSection.hidden = false;

  resultSection.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth",
    block: "start",
  });
}

async function analyzeMessage() {
  clearError();
  const message = input.value.trim();

  if (!message) {
    showError("Paste a message before submitting the artifact.");
    input.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data?.error?.message || "The artifact could not be analyzed."
      );
    }

    renderResult(data);
  } catch (error) {
    showError(
      error instanceof Error
        ? error.message
        : "The artifact could not be analyzed."
    );
  } finally {
    setLoading(false);
  }
}

input.addEventListener("input", updateCharacterCount);

input.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    analyzeMessage();
  }
});

analyzeButton.addEventListener("click", analyzeMessage);

analyzeAnother.addEventListener("click", () => {
  resultSection.hidden = true;
  input.focus();

  document.getElementById("analyzer").scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth",
  });
});

updateCharacterCount();

import("/static/js/ocr.js").catch((error) => {
  console.warn("Screenshot OCR adapter could not be loaded.", error);
});
