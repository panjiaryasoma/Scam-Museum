# SCAM MUSEUM — REPOSITORY STRUCTURE

**Version:** 0.1  
**Status:** Proposed / Pre-Production  
**Goal:** Minimal repository for a 1–2 day HackSocial build.

```text
scam-museum/
├── api/
│   └── .gitkeep
│
├── app/
│   ├── core/
│   │   └── .gitkeep
│   ├── templates/
│   │   └── .gitkeep
│   └── static/
│       ├── css/
│       │   └── .gitkeep
│       ├── js/
│       │   └── .gitkeep
│       └── assets/
│           └── .gitkeep
│
├── ml/
│   └── .gitkeep
│
├── models/
│   └── .gitkeep
│
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   ├── processed/
│   │   └── .gitkeep
│   └── samples/
│       └── .gitkeep
│
├── tests/
│   └── .gitkeep
│
├── scripts/
│   └── .gitkeep
│
├── docs/
│   ├── 01_problem/
│   │   └── SCAM_MUSEUM_PROBLEM_BRIEF_v0.1.md
│   ├── 02_product/
│   │   └── SCAM_MUSEUM_SIMPLE_PRD_v0.1.md
│   └── 03_data_eval/
│       ├── DATASET_STRATEGY.md
│       └── EVALUATION_CONTRACT.md
│
├── reports/
│   └── .gitkeep
│
├── submission/
│   ├── screenshots/
│   │   └── .gitkeep
│   └── devpost/
│       └── .gitkeep
│
├── .gitignore
├── README.md
└── requirements.txt
```

## Folder Responsibilities

### `api/`
Vercel entrypoint nanti. Idealnya hanya adapter tipis yang mengimpor FastAPI app dari `app/`.

### `app/`
Production web application.

- `core/` — inference, evidence extraction, risk mapping, exhibit generation, schemas.
- `templates/` — Jinja/HTML pages.
- `static/css/` — final museum UI styles.
- `static/js/` — browser interactions.
- `static/assets/` — branding, local images, exhibit assets.

### `ml/`
Training-side code only.

Nanti berisi misalnya:
- dataset loading / preprocessing;
- baseline training;
- final training;
- evaluation.

Runtime web app tidak perlu bergantung pada training code.

### `models/`
Final committed model artifact dan metadata setelah model lock.

Contoh nanti:
```text
models/
├── scam_classifier.joblib
└── model_metadata.json
```

### `data/`
- `raw/` — local source datasets; jangan commit dataset besar atau yang lisensinya tidak mengizinkan.
- `processed/` — generated training/evaluation data.
- `samples/` — curated/sanitized demo messages yang aman untuk repo dan UI.

### `tests/`
Minimal regression coverage untuk:
- inference;
- evidence extraction;
- exhibit generation;
- API/input validation.

### `scripts/`
One-off reproducibility helpers saja. Jangan berubah menjadi folder kuburan script.

### `docs/`
Dokumen pre-production dan source of truth.

### `reports/`
Hasil model/evaluation yang layak ditunjukkan juri:
- metrics;
- confusion matrix output;
- failure analysis;
- limitation notes.

### `submission/`
Asset Devpost saja:
- screenshot;
- final project copy;
- optional gallery assets.

Bukan bagian runtime.

---

## Planned Production Files

File berikut **belum dibuat** sampai gate data/evaluation selesai:

```text
api/index.py

app/main.py
app/core/schemas.py
app/core/text.py
app/core/inference.py
app/core/evidence.py
app/core/risk.py
app/core/exhibit.py

app/templates/index.html
app/static/css/app.css
app/static/js/app.js

ml/prepare_data.py
ml/train.py
ml/evaluate.py

tests/test_inference.py
tests/test_evidence.py
tests/test_api.py

models/scam_classifier.joblib
models/model_metadata.json

vercel.json
```

Jangan membuat modul baru kecuali ada kebutuhan nyata.

---

## Architecture Boundary

```text
TRAINING SIDE

data/
  ↓
ml/
  ↓
models/scam_classifier.joblib
          │
          │ final artifact
          ▼

RUNTIME SIDE

User
 ↓
app/main.py
 ↓
validation / normalization
 ↓
app/core/inference.py ─── loads ─── models/
 ↓
app/core/evidence.py
 ↓
app/core/risk.py
 ↓
app/core/exhibit.py
 ↓
HTML exhibit
```

Machine-learning prediction dan deterministic evidence extraction tetap dipisahkan.

---

## Scope Rule

Untuk HackSocial v1, repository tidak membutuhkan:

- database;
- authentication;
- Docker;
- background worker;
- React build pipeline;
- microservices;
- message queue;
- cloud storage;
- vector database;
- LLM orchestration.

Jika sebuah folder baru tidak membantu **Technical Execution**, **Innovation & Creativity**, atau **UI & Design**, kemungkinan besar folder itu tidak dibutuhkan.
