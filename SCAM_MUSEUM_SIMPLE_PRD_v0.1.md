# SCAM MUSEUM — SIMPLE PRD

**Version:** 0.1  
**Status:** Scope Draft  
**Hackathon:** HackSocial 2026  
**Track:** AI / ML  
**Date:** 29 August 2026

---

## 1. Product Summary

**Scam Museum** adalah web app AI/ML yang mengubah pesan mencurigakan menjadi **museum exhibit**.

User paste satu pesan. Sistem kemudian:

1. mengklasifikasikan risiko scam menggunakan NLP/ML;
2. mendeteksi manipulation signals yang dapat diperiksa;
3. menyorot bagian pesan yang mencurigakan;
4. menyajikan hasil sebagai exhibit bergaya museum.

Core idea:

> **classification → evidence → educational exhibit**

Scam Museum bukan sistem penentu kebenaran dan tidak boleh menyatakan bahwa suatu pesan **pasti** scam.

---

## 2. Primary User

Pengguna internet yang menerima pesan mencurigakan melalui:

- SMS;
- email;
- messaging apps;
- direct message.

Target user tidak diasumsikan memahami cybersecurity atau machine learning.

---

## 3. Core Job to Be Done

> Ketika menerima pesan yang terasa mencurigakan, user ingin tahu apakah pesan tersebut menunjukkan pola scam, bagian mana yang mencurigakan, dan teknik manipulasi apa yang digunakan.

---

## 4. Core User Flow

```text
Paste message
     ↓
Validate input
     ↓
Normalize text
     ↓
ML scam-risk classification
     ↓
Detect manipulation signals
     ↓
Extract suspicious fragments
     ↓
Generate museum exhibit
     ↓
Show result
```

Satu input.  
Satu action.  
Satu result utama.

---

## 5. MVP Scope

### P0 — Must Have

- paste text input;
- English-first message analysis;
- trained binary ML classifier;
- `SCAM` / `LEGITIMATE` internal prediction;
- user-facing risk band:
  - `LOW RISK`
  - `SUSPICIOUS`
  - `HIGH RISK`
- manipulation-signal detection;
- suspicious fragment highlighting;
- museum-style exhibit result;
- plain-language explanation;
- curated sample messages;
- responsive UI;
- model evaluation;
- basic inference/regression tests;
- public GitHub repository;
- Vercel deployment.

### P1 — Only If P0 Stable

- Indonesian language support;
- screenshot upload;
- OCR;
- shareable exhibit card;
- richer scam taxonomy.

---

## 6. Explicit Non-Goals

MVP tidak mencakup:

- login;
- user accounts;
- database/history;
- WhatsApp bot;
- browser extension;
- crowdsourced scam database;
- live threat intelligence;
- automatic URL opening;
- real-time sender verification;
- generic chatbot;
- universal multilingual support;
- automatic scam reporting.

---

## 7. AI / ML Contract

### Primary task

Binary text classification:

```text
SCAM
LEGITIMATE
```

### Initial model candidate

```text
Text normalization
        ↓
TF-IDF
        ↓
Logistic Regression
```

Model final ditentukan setelah benchmark.

### Language scope

**v1: English-first.**

Indonesian hanya ditambahkan bila dataset dan evaluation cukup layak.

Tidak boleh mengklaim multilingual sebelum diuji per bahasa.

---

## 8. Evidence Layer

Explanation tidak seluruhnya berasal dari ML model.

Deterministic evidence layer dapat mendeteksi:

- urgency;
- reward bait;
- credential / OTP request;
- suspicious links;
- financial request;
- authority impersonation indicators.

UI harus membedakan:

```text
ML prediction
Detected evidence signals
```

Rule signal tidak boleh dipresentasikan sebagai causal explanation dari model bila memang bukan.

---

## 9. Output Contract

Satu result minimal berisi:

```text
Exhibit title
Risk band
ML prediction
Detected manipulation signals
Highlighted suspicious fragments
Plain-language explanation
Exhibit metadata
Safety note
```

Contoh:

```text
THE URGENCY TRAP
Unknown Scammer, 2026

Risk: HIGH

Observed signals:
- Artificial urgency
- Credential request
- Reward bait
- Suspicious link
```

---

## 10. UX Direction

Visual language:

> **museum gallery × editorial archive × digital fraud artifact**

UI tidak boleh terlihat seperti dashboard cybersecurity generik.

Core interaction harus terasa seperti user sedang **examining an artifact**, bukan mengisi form enterprise.

Primary visual motif:

- framed message;
- museum plaque;
- accession number;
- exhibit title;
- curatorial notes.

---

## 11. Claim Boundary

Scam Museum tidak boleh menampilkan klaim seperti:

> “This message is definitely a scam.”

Preferred wording:

> “This message contains multiple signals commonly associated with scams.”

Jika probability model tidak cukup reliable, UI memakai **risk bands** tanpa angka persentase.

---

## 12. Safety Requirements

- jangan membuka suspicious links secara otomatis;
- jangan meminta password, OTP, atau credential asli;
- curated examples harus synthetic atau sanitized;
- jangan menampilkan PII nyata;
- jangan mendorong user membalas atau berinteraksi dengan scammer.

---

## 13. Success Criteria

### Product

- user dapat paste pesan dan menerima exhibit;
- result dapat dipahami tanpa dokumentasi;
- evidence terlihat jelas;
- museum concept konsisten.

### ML

- dataset provenance terdokumentasi;
- train/test split jelas;
- baseline tersedia;
- final model dievaluasi pada holdout set;
- metric dilaporkan jujur;
- tidak ada known leakage.

### Engineering

- aplikasi dapat dijalankan dari repo;
- model artifact dapat dimuat reproducibly;
- invalid input ditangani;
- deployed app dapat dipakai tanpa setup lokal.

### Hackathon

Produk harus kuat pada:

- **Technical Execution**
- **Innovation & Creativity**
- **User Interface and Design**

---

## 14. Release Gate

Sebelum production dianggap selesai:

```text
[ ] Dataset locked
[ ] Evaluation contract locked
[ ] Baseline trained
[ ] Final model selected
[ ] Evidence layer tested
[ ] Core UI complete
[ ] Vercel deployment working
[ ] README complete
[ ] Devpost description updated
[ ] Submission checked before internal deadline
```

---

## 15. Scope Decision

Scam Museum v1 adalah:

> **A small, explainable ML-powered web experience for examining suspicious messages as museum artifacts of digital manipulation.**

Focus:

```text
ONE MESSAGE
ONE CLASSIFICATION
VISIBLE EVIDENCE
ONE MEMORABLE EXHIBIT
```

Tidak lebih.
