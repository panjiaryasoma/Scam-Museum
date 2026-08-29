const shareButton = document.getElementById("share-exhibit");
const shareStatus = document.getElementById("share-status");

const SHARE_CARD = {
  width: 1080,
  height: 1350,
  margin: 72,
  background: "#171412",
  surface: "#1c1917",
  raised: "#24201d",
  border: "#47413c",
  text: "#f5f5f4",
  secondary: "#c7c2bd",
  tertiary: "#8f8881",
};

const VERDICT_COLORS = {
  "HIGH RISK": { border: "#7f1d1d", fill: "#31181a", text: "#fca5a5" },
  SUSPICIOUS: { border: "#854d0e", fill: "#2e2814", text: "#fde047" },
  "LOW RISK": { border: "#3f6212", fill: "#1f2b17", text: "#bef264" },
  "INSUFFICIENT EVIDENCE": { border: "#78716c", fill: "#292521", text: "#c7c2bd" },
};

function setShareStatus(message) {
  if (shareStatus) {
    shareStatus.textContent = message;
  }
}

function roundedText(ctx, text, x, y, maxWidth, lineHeight, maxLines = Infinity) {
  const words = String(text || "").trim().split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";

  for (const word of words) {
    const test = current ? `${current} ${word}` : word;
    if (ctx.measureText(test).width <= maxWidth || !current) {
      current = test;
      continue;
    }

    lines.push(current);
    current = word;
  }

  if (current) {
    lines.push(current);
  }

  const visible = lines.slice(0, maxLines);
  if (lines.length > maxLines && visible.length) {
    let last = visible[visible.length - 1];
    while (last.length && ctx.measureText(`${last}…`).width > maxWidth) {
      last = last.slice(0, -1);
    }
    visible[visible.length - 1] = `${last.trim()}…`;
  }

  visible.forEach((line, index) => {
    ctx.fillText(line, x, y + index * lineHeight);
  });

  return y + visible.length * lineHeight;
}

function drawRule(ctx, y) {
  ctx.strokeStyle = SHARE_CARD.border;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(SHARE_CARD.margin, y);
  ctx.lineTo(SHARE_CARD.width - SHARE_CARD.margin, y);
  ctx.stroke();
}

function getFindingLabels() {
  return Array.from(document.querySelectorAll("#evidence-list .finding-item strong"))
    .map((node) => node.textContent?.trim())
    .filter(Boolean)
    .slice(0, 4);
}

function getSharePayload() {
  const title = document.getElementById("exhibit-title")?.textContent?.trim() || "Unclassified artifact";
  const verdict = document.getElementById("verdict-text")?.textContent?.trim() || "—";
  const ml = document.getElementById("ml-signal")?.textContent?.trim() || "ML risk signal: —";
  const message = document.getElementById("highlighted-message")?.textContent?.trim() || "";
  const note = document.getElementById("curatorial-note")?.textContent?.trim() || "";
  const findings = getFindingLabels();

  return { title, verdict, ml, message, note, findings };
}

function drawVerdict(ctx, verdict) {
  const palette = VERDICT_COLORS[verdict] || VERDICT_COLORS["INSUFFICIENT EVIDENCE"];
  const width = 280;
  const height = 116;
  const x = SHARE_CARD.width - SHARE_CARD.margin - width;
  const y = 150;

  ctx.fillStyle = palette.fill;
  ctx.strokeStyle = palette.border;
  ctx.lineWidth = 1;
  ctx.fillRect(x, y, width, height);
  ctx.strokeRect(x, y, width, height);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 20px Inter, Arial, sans-serif';
  ctx.fillText("ASSESSMENT", x + 24, y + 38);

  ctx.fillStyle = palette.text;
  ctx.font = '600 24px Inter, Arial, sans-serif';
  roundedText(ctx, verdict, x + 24, y + 78, width - 48, 28, 2);
}

async function buildShareCardBlob() {
  if (document.fonts?.ready) {
    await document.fonts.ready;
  }

  const data = getSharePayload();
  const canvas = document.createElement("canvas");
  canvas.width = SHARE_CARD.width;
  canvas.height = SHARE_CARD.height;

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Canvas rendering is not available in this browser.");
  }

  ctx.fillStyle = SHARE_CARD.background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = SHARE_CARD.border;
  ctx.lineWidth = 1;
  ctx.strokeRect(34, 34, canvas.width - 68, canvas.height - 68);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 20px Inter, Arial, sans-serif';
  ctx.fillText("SCAM MUSEUM / GALLERY OF DIGITAL DECEPTION", SHARE_CARD.margin, 92);
  ctx.fillText("ACCESSION NO. SM.2026.001", SHARE_CARD.margin, 132);

  drawVerdict(ctx, data.verdict);

  ctx.fillStyle = SHARE_CARD.text;
  ctx.font = '700 58px "Libre Baskerville", Georgia, serif';
  roundedText(ctx, data.title.toUpperCase(), SHARE_CARD.margin, 205, 650, 70, 3);

  drawRule(ctx, 340);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 20px Inter, Arial, sans-serif';
  ctx.fillText("SUBMITTED ARTIFACT", SHARE_CARD.margin, 390);
  ctx.textAlign = "right";
  ctx.fillText(data.ml.toUpperCase(), SHARE_CARD.width - SHARE_CARD.margin, 390);
  ctx.textAlign = "left";

  const boxX = SHARE_CARD.margin;
  const boxY = 430;
  const boxW = SHARE_CARD.width - SHARE_CARD.margin * 2;
  const boxH = 430;

  ctx.fillStyle = SHARE_CARD.raised;
  ctx.strokeStyle = SHARE_CARD.border;
  ctx.fillRect(boxX, boxY, boxW, boxH);
  ctx.strokeRect(boxX, boxY, boxW, boxH);

  ctx.fillStyle = SHARE_CARD.text;
  ctx.font = '400 36px "Libre Baskerville", Georgia, serif';
  roundedText(ctx, data.message, boxX + 38, boxY + 70, boxW - 76, 56, 6);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 20px Inter, Arial, sans-serif';
  ctx.fillText("OBSERVED ARTIFACTS", SHARE_CARD.margin, 918);

  if (data.findings.length) {
    ctx.fillStyle = SHARE_CARD.text;
    ctx.font = '600 24px Inter, Arial, sans-serif';

    data.findings.forEach((finding, index) => {
      const column = index % 2;
      const row = Math.floor(index / 2);
      const x = SHARE_CARD.margin + column * 468;
      const y = 970 + row * 58;

      ctx.fillStyle = SHARE_CARD.tertiary;
      ctx.font = '600 18px Inter, Arial, sans-serif';
      ctx.fillText(String(index + 1).padStart(2, "0"), x, y);

      ctx.fillStyle = SHARE_CARD.text;
      ctx.font = '600 23px Inter, Arial, sans-serif';
      roundedText(ctx, finding, x + 40, y, 390, 28, 1);
    });
  } else {
    ctx.fillStyle = SHARE_CARD.secondary;
    ctx.font = '400 24px Inter, Arial, sans-serif';
    ctx.fillText("No material observable risk artifacts were cataloged.", SHARE_CARD.margin, 970);
  }

  drawRule(ctx, 1095);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 20px Inter, Arial, sans-serif';
  ctx.fillText("CURATORIAL NOTE", SHARE_CARD.margin, 1144);

  ctx.fillStyle = SHARE_CARD.secondary;
  ctx.font = '400 24px Inter, Arial, sans-serif';
  roundedText(ctx, data.note, SHARE_CARD.margin, 1187, SHARE_CARD.width - SHARE_CARD.margin * 2, 36, 2);

  ctx.fillStyle = SHARE_CARD.tertiary;
  ctx.font = '600 18px Inter, Arial, sans-serif';
  ctx.fillText("EVERY SCAM LEAVES ARTIFACTS.", SHARE_CARD.margin, 1290);
  ctx.textAlign = "right";
  ctx.fillText("SCAM MUSEUM · 2026", SHARE_CARD.width - SHARE_CARD.margin, 1290);
  ctx.textAlign = "left";

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("The exhibit card could not be rendered."));
      }
    }, "image/png");
  });
}

function slugify(value) {
  return String(value || "exhibit")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "exhibit";
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function shareExhibit() {
  if (!shareButton) {
    return;
  }

  shareButton.disabled = true;
  setShareStatus("Preparing exhibit card…");

  try {
    const data = getSharePayload();
    const blob = await buildShareCardBlob();
    const filename = `scam-museum-${slugify(data.title)}.png`;
    const file = new File([blob], filename, { type: "image/png" });
    const shareData = {
      files: [file],
      title: `Scam Museum: ${data.title}`,
      text: `${data.title} — ${data.verdict}`,
    };

    if (navigator.share && navigator.canShare?.(shareData)) {
      try {
        await navigator.share(shareData);
        setShareStatus("Exhibit shared.");
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          setShareStatus("");
          return;
        }
        throw error;
      }
    } else {
      downloadBlob(blob, filename);
      setShareStatus("Exhibit card downloaded.");
    }
  } catch (error) {
    console.error("Share card error", error);
    setShareStatus("Could not prepare the exhibit card.");
  } finally {
    shareButton.disabled = false;
  }
}

shareButton?.addEventListener("click", shareExhibit);
