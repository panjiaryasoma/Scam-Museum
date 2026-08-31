const EXHIBITS = [
  {
    accession: "SM.2026.018",
    title: "The Urgency Trap",
    family: "Banking",
    familyKey: "banking",
    risk: "High Risk",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Security Alert\n\nYour account has been suspended due to suspicious activity. Verify within 24 hours or access will be permanently locked.\n\nVerify now: secure-login-id.example",
    evidence: ["TIME_URGENCY", "ACCOUNT_THREAT", "SUSPICIOUS_URL", "AUTHORITY_CLAIM"],
    note: "This reconstructed exhibit demonstrates how account-loss pressure and a verification link can work together. The message creates a deadline, invokes a security role, and moves the recipient toward an external interaction."
  },
  {
    accession: "SM.2026.011",
    title: "The False Banker",
    family: "Impersonation",
    familyKey: "impersonation",
    risk: "High Risk",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Bank Support Team\n\nWe noticed unusual activity on your account. Please confirm your card details and verification code so we can keep your account safe.",
    evidence: ["AUTHORITY_CLAIM", "FINANCIAL_INFO_REQUEST", "OTP_REQUEST"],
    note: "The exhibit combines institutional impersonation with requests for authentication and financial information. The authoritative framing is not proof of identity; the operational requests are the observable artifacts."
  },
  {
    accession: "SM.2026.027",
    title: "The Paid Task Pitch",
    family: "Job Scam",
    familyKey: "job",
    risk: "High Risk",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Work From Home\n\nComplete simple rating tasks and earn $50–$200 per day. No experience needed. Reply YES to receive your first paid task.",
    evidence: ["REPLY_OR_CALL_REQUEST", "NEED_AND_GREED", "JOB_TASK_SOLICITATION", "PIECE_RATE_TASK_PAYMENT"],
    note: "This exhibit reconstructs the opening stage of a task scam: easy work, unusually attractive pay, and a request to continue the conversation. Later stages of this scam family may introduce deposits or withdrawal fees."
  },
  {
    accession: "SM.2026.034",
    title: "The Parcel Gate",
    family: "Delivery",
    familyKey: "delivery",
    risk: "High Risk",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Delivery Service\n\nYour parcel is being held because the delivery fee is unpaid. Pay the $2.75 release fee today to avoid return to sender.",
    evidence: ["AUTHORITY_CLAIM", "PAYMENT_REQUEST", "TIME_URGENCY"],
    note: "Small fees can reduce hesitation. This reconstruction pairs a low payment request with delivery authority and time pressure, a common structure in parcel-themed phishing."
  },
  {
    accession: "SM.2026.041",
    title: "The New Number",
    family: "Family Impersonation",
    familyKey: "family",
    risk: "Suspicious",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Hi Mum, it's me. My phone broke and this is my temporary number. Can you message me back when you see this?",
    evidence: ["FAMILY_IMPERSONATION", "NEW_NUMBER_CLAIM", "REPLY_OR_CALL_REQUEST"],
    note: "A new-number claim is not automatically fraudulent. The exhibit is cataloged as suspicious because family identity and contact migration appear together, but independent verification is still necessary."
  },
  {
    accession: "SM.2026.052",
    title: "The Accidental Hello",
    family: "Wrong Number",
    familyKey: "wrong-number",
    risk: "Insufficient Evidence",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Hi Anna, are we still meeting this afternoon?\n\nOh sorry, wrong number. You seem kind though. What city are you in?",
    evidence: ["UNEXPECTED_CONTACT"],
    note: "Wrong-number conversations can be harmless or become grooming funnels. This exhibit intentionally preserves uncertainty because the opening alone does not justify a high-risk conclusion."
  },
  {
    accession: "SM.2026.063",
    title: "The Official Deadline",
    family: "Government",
    familyKey: "government",
    risk: "High Risk",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Revenue Service Notice\n\nA penalty is pending on your account. Payment is required immediately to prevent further enforcement. Contact this number now to resolve the balance.",
    evidence: ["AUTHORITY_CLAIM", "PAYMENT_REQUEST", "TIME_URGENCY", "REPLY_OR_CALL_REQUEST"],
    note: "The exhibit uses official-sounding authority, a threatened consequence, and immediate payment/contact instructions. These observable behaviors matter more than the claimed institutional identity."
  },
  {
    accession: "SM.2026.071",
    title: "The Reward Door",
    family: "Telecom",
    familyKey: "telecom",
    risk: "Suspicious",
    year: "2026",
    sourceType: "Reconstructed demonstration",
    medium: "Synthetic digital message",
    message: "Mobile Rewards\n\nCongratulations. Your loyalty account qualifies for a special refund. Reply now to claim your reward before it expires.",
    evidence: ["NEED_AND_GREED", "TIME_URGENCY", "REPLY_OR_CALL_REQUEST"],
    note: "Unexpected rewards and expiring opportunities are persuasion devices. This reconstruction shows how a benefit lure can push the recipient into continuing contact without yet containing a critical credential or payment request."
  }
];

const galleryGrid = document.getElementById("exhibit-grid");
const galleryEmpty = document.getElementById("collection-empty");
const filterButtons = Array.from(document.querySelectorAll("[data-gallery-filter]"));
const collectionCount = document.getElementById("collection-count");
const dialog = document.getElementById("exhibit-dialog");
const dialogClose = document.getElementById("dialog-close");
const dialogAccession = document.getElementById("dialog-accession");
const dialogTitle = document.getElementById("dialog-title");
const dialogMeta = document.getElementById("dialog-meta");
const dialogMessage = document.getElementById("dialog-message");
const dialogFamily = document.getElementById("dialog-family");
const dialogRisk = document.getElementById("dialog-risk");
const dialogSource = document.getElementById("dialog-source");
const dialogMedium = document.getElementById("dialog-medium");
const dialogArtifacts = document.getElementById("dialog-artifacts");
const dialogNote = document.getElementById("dialog-note");
const viewSimilar = document.getElementById("view-similar-exhibits");

let activeFilter = "all";
let latestEvidence = [];

function normalizeEvidenceLabel(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function makeCard(exhibit) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "exhibit-card";
  button.dataset.family = exhibit.familyKey;
  button.dataset.accession = exhibit.accession;
  button.dataset.evidence = exhibit.evidence.join(" ");
  button.setAttribute("aria-label", `Open exhibit ${exhibit.title}`);

  const art = document.createElement("div");
  art.className = "exhibit-card-art";

  const frame = document.createElement("div");
  frame.className = "exhibit-mini-frame";

  const message = document.createElement("div");
  message.className = "exhibit-mini-message";
  message.textContent = exhibit.message;
  frame.append(message);
  art.append(frame);

  const info = document.createElement("div");
  info.className = "exhibit-card-info";

  const accession = document.createElement("span");
  accession.className = "exhibit-accession";
  accession.textContent = exhibit.accession;

  const title = document.createElement("h3");
  title.textContent = exhibit.title;

  const meta = document.createElement("p");
  meta.className = "exhibit-meta";
  meta.textContent = `${exhibit.family} · ${exhibit.risk}`;

  const footer = document.createElement("div");
  footer.className = "exhibit-card-footer";
  footer.innerHTML = `<span>${exhibit.sourceType}</span><span>View record ↗</span>`;

  info.append(accession, title, meta, footer);
  button.append(art, info);
  button.addEventListener("click", () => openExhibit(exhibit));

  return button;
}

function openExhibit(exhibit) {
  if (!dialog) return;

  dialogAccession.textContent = exhibit.accession;
  dialogTitle.textContent = exhibit.title;
  dialogMeta.textContent = `${exhibit.family} · ${exhibit.risk}`;
  dialogMessage.textContent = exhibit.message;
  dialogFamily.textContent = exhibit.family;
  dialogRisk.textContent = exhibit.risk;
  dialogSource.textContent = exhibit.sourceType;
  dialogMedium.textContent = exhibit.medium;
  dialogNote.textContent = exhibit.note;
  dialogArtifacts.replaceChildren();

  exhibit.evidence.forEach((item) => {
    const chip = document.createElement("span");
    chip.textContent = normalizeEvidenceLabel(item);
    dialogArtifacts.append(chip);
  });

  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
}

function renderGallery() {
  if (!galleryGrid) return;

  galleryGrid.replaceChildren();
  const visible = EXHIBITS.filter((exhibit) => {
    if (activeFilter === "similar") {
      if (!latestEvidence.length) return true;
      return exhibit.evidence.some((item) => latestEvidence.includes(item));
    }
    return activeFilter === "all" || exhibit.familyKey === activeFilter;
  });

  visible.forEach((exhibit) => galleryGrid.append(makeCard(exhibit)));

  if (galleryEmpty) galleryEmpty.hidden = visible.length > 0;
  if (collectionCount) {
    const label = activeFilter === "similar" ? "related exhibits" : "curated exhibits";
    collectionCount.textContent = `${visible.length} ${label}`;
  }
}

function selectFilter(nextFilter) {
  activeFilter = nextFilter;
  filterButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.galleryFilter === nextFilter));
  });
  renderGallery();
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => selectFilter(button.dataset.galleryFilter || "all"));
});

dialogClose?.addEventListener("click", () => dialog.close());
dialog?.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && dialog?.open) dialog.close();
});

window.addEventListener("scam-museum:analysis-rendered", (event) => {
  const evidence = event.detail?.evidence || [];
  latestEvidence = evidence.map((item) => item.id).filter(Boolean);
  if (viewSimilar) viewSimilar.hidden = false;
});

viewSimilar?.addEventListener("click", () => {
  activeFilter = "similar";
  filterButtons.forEach((button) => button.setAttribute("aria-pressed", "false"));
  renderGallery();
  document.getElementById("collection")?.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "start"
  });
});

renderGallery();
