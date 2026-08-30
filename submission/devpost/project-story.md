# Scam Museum

**Every scam leaves artifacts.**

## Inspiration

Most scam detectors reduce a suspicious message to a binary answer: scam or not scam. That is convenient, but it hides the part that matters to a person making a decision: **what in the message actually looks risky?**

Scam Museum started from a simple idea: treat a suspicious message like an exhibit. Instead of presenting an opaque score as truth, catalog the observable artifacts of deception, show the exact passages that triggered them, and allow the system to remain uncertain when the text does not justify a confident verdict.

The museum metaphor is not decoration. It shapes the product. A message becomes an artifact, risk indicators become cataloged evidence, and the final result becomes a curatorial explanation rather than a red or green badge pretending to know the sender's intent.

## What it does

Scam Museum analyzes suspicious digital messages through a hybrid ML + evidence pipeline.

A user can paste text, upload a screenshot, or paste a screenshot directly from the clipboard. Screenshot text is extracted in the browser with Tesseract.js, then returned to the normal message box so the user can review and correct it before analysis.

The reviewed message is processed by two separate layers:

1. a frozen v0.5 machine-learning classifier that produces a `WEAK`, `ELEVATED`, or `STRONG` text-risk signal; and
2. a deterministic evidence engine that looks for observable behaviors such as OTP requests, money-transfer requests, payment requests, suspicious links, urgency, impersonation cues, risky attachments, job/task solicitations, and protective warnings.

Those signals are resolved through an explicit uncertainty-aware decision layer. The user sees one of four assessments:

- `LOW RISK`
- `INSUFFICIENT EVIDENCE`
- `SUSPICIOUS`
- `HIGH RISK`

The interface highlights the exact text fragments associated with detected evidence and presents the result as a museum-style exhibit with an exhibit title, cataloged artifacts, and a curatorial note. The exhibit can also be exported as a shareable image card without storing the analyzed message on a server.

## How we built it

The application uses FastAPI for the backend and plain HTML, CSS, and JavaScript for the frontend. The ML runtime is built with scikit-learn.

The frozen v0.5 classifier, `word_char_balanced_v05`, combines word-level TF-IDF features with character `char_wb` TF-IDF features and logistic regression with balanced class weights. The final decision threshold is frozen at `0.80`.

The final training corpus contains 12,885 messages:

- 4,212 legitimate / hard-negative messages
- 8,673 scam-risk messages

### Core Decision Flow

<img width="1162" height="2788" alt="E2E_Diagram" src="https://github.com/user-attachments/assets/ad9ad407-3d2c-442c-96e1-3315c019c161" />

The end-to-end pipeline takes reviewed message text through preparation, ML risk signaling, deterministic evidence detection, explicit uncertainty handling, and final museum-style presentation. Screenshot input joins the same path after browser-side OCR and user review.

<img width="2211" height="6746" alt="Flowchart" src="https://github.com/user-attachments/assets/cb210a2e-3b96-4ccc-906c-a7131077c036" />

The system flowchart shows the operational decision path from text or screenshot input to validation, evidence-aware assessment, exhibit generation, optional sharing, and human verification. Each final verdict is produced by the same decision contract rather than by the classifier alone.

### Architecture

<img width="2682" height="2570" alt="Architecture" src="https://github.com/user-attachments/assets/3ba7848f-8c79-4c01-8152-21aeaeee2c72" />

Scam Museum separates browser-side OCR and share-card rendering from the FastAPI analysis service. The backend combines the frozen v0.5 model artifact, deterministic evidence rules, contextual and protective evidence, and the uncertainty-aware decision contract before returning structured exhibit metadata.

Model selection was deliberately broader than a single random train/test split. We compared candidates using grouped out-of-fold performance on the primary dataset, leave-one-scam-family-out recall on newer scam families, and leave-one-negative-source-out specificity on legitimate-but-scam-like messages. Only after model and threshold selection did we evaluate the original locked test set.

On the 1,079-message locked test set, v0.5 produced:

| Metric | Result |
|---|---:|
| F1 macro | 0.9505 |
| Scam precision | 0.9604 |
| Scam recall | 0.8661 |
| Scam F1 | 0.9108 |
| Specificity | 0.9959 |
| Balanced accuracy | 0.9310 |
| Average precision | 0.9648 |

The locked-test confusion matrix was:

```text
                 Predicted legit   Predicted scam
Actual legit            963               4
Actual scam              15              97
```

The ML output is intentionally not shown as a calibrated probability. Scam Museum calls it an **ML risk signal**, because a classifier score is useful evidence but not proof of real-world intent.

The second half of the system is deterministic. Evidence rules are kept separate from ML inference so the interface can distinguish between "the model considers this text risky" and "this exact phrase contains an OTP request." Protective evidence is also modeled, because a legitimate security warning such as "we will never ask for your password" should not be treated the same way as a request to send a password.

For screenshots, OCR runs client-side with Tesseract.js. The screenshot itself is not sent into the classifier. Users review the extracted text first, which prevents OCR noise from being silently treated as ground truth.

The result page is rendered as a museum exhibit and can be converted into a shareable image card in the browser.

## Challenges we ran into

### A model that looked strong was still brittle

Early versions performed extremely well on the original smishing benchmark, but external scam-family testing exposed a serious domain-shift problem. Conversational scams, wrong-number approaches, family impersonation, and modern task scams did not always resemble classic phishing SMS.

That changed the project. Instead of optimizing one benchmark until the number looked impressive, we rebuilt the evaluation around scam-family generalization and hard negatives.

### High recall created uncomfortable false positives

A scam detector that flags every suspicious-looking sentence is not useful. Security notices, delivery updates, family messages, and ordinary requests for money can contain vocabulary that also appears in scams.

We added hard-negative development data, protective evidence, and explicit ambiguity handling. `INSUFFICIENT EVIDENCE` exists because forcing every message into safe/scam was producing confident answers the text did not actually support.

### Evidence is not the same as intent

A phrase such as "transfer the money" is observable. Whether the sender is a criminal is not observable from that phrase alone. We had to keep the evidence layer strict about this distinction, both in the runtime logic and in the language shown to users.

### OCR had to remain reviewable

Screenshot support is convenient, but OCR can make transcription mistakes. Rather than hiding the OCR step, Scam Museum exposes the extracted text and asks the user to review it before analysis.

### Keeping the interface understandable

The system has ML output, deterministic evidence, protective evidence, uncertainty, highlighted passages, and a final verdict. Presenting all of that without turning the page into a security dashboard was a design problem of its own. The museum metaphor gave us a coherent information hierarchy.

## Accomplishments that we're proud of

We are most proud that Scam Museum does not pretend its classifier is an oracle.

The final application has a frozen ML model, deterministic evidence extraction, protective-evidence handling, explicit uncertainty, screenshot OCR, clipboard image paste, text highlighting, and shareable exhibit cards in one coherent workflow.

The full automated suite currently contains **199 passing tests**, covering the API, evidence rules, risk decisions, ambiguity behavior, exhibit titles, OCR integration, and regression contracts.

We also ran a separate behavioral audit on 24 hand-reviewed realistic chat cases. The complete application decision layer matched the review target on 21 of 24 cases, or 87.5%. We treat that number as an audit match rate, not population-level accuracy.

More importantly, the audit exposed failure modes we could inspect instead of hiding them behind a headline metric.

## What we learned

The biggest lesson was that **classification quality and product decision quality are not the same problem**.

A model can score well while still behaving poorly on a new scam family. A phrase can be statistically suspicious while still being harmless in context. A deterministic rule can identify an observable request without proving malicious intent.

That led to the architecture we ended with: ML as a signal, evidence as observable behavior, counter-evidence as a first-class input, and uncertainty as a valid output.

We also learned that evaluation design matters as much as model choice. Grouped splits, family holdouts, hard negatives, frozen thresholds, and behavioral regression cases gave us more useful information than repeatedly chasing a higher random-split accuracy score.

## What's next

Scam Museum is still a hackathon prototype, not a production fraud-verification service.

The next steps are to expand beyond English-first SMS-style messages, add stronger conversation-context handling, improve OCR robustness on noisy screenshots, evaluate calibrated uncertainty, and explore optional live domain or URL reputation signals without mixing those claims into the local evidence layer.

We also want to expand the museum itself: a browsable collection of scam patterns, each grounded in examples and evidence rather than generic fear-based warnings.

## Built with

- Python 3.12
- FastAPI
- scikit-learn
- TF-IDF + Logistic Regression
- NumPy / SciPy
- joblib
- HTML / CSS / vanilla JavaScript
- Tesseract.js
- pytest
- Vercel

---

**Scam Museum**  
*Gallery of Digital Deception*  
**Every scam leaves artifacts.**
