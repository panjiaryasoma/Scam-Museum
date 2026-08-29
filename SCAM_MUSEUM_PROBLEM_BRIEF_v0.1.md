# SCAM MUSEUM — PROBLEM BRIEF

**Version:** 0.1  
**Status:** Draft for Scope Lock  
**Project:** Scam Museum  
**Hackathon:** HackSocial 2026  
**Track:** AI / ML  
**Date:** 29 August 2026

---

## 1. Problem Summary

Pesan scam, phishing, impersonation, dan social-engineering sering menggunakan pola manipulasi yang berulang: urgency, reward bait, credential requests, authority impersonation, fear, scarcity, dan suspicious links.

Masalahnya bukan hanya apakah sebuah pesan dapat diklasifikasikan sebagai scam.

Pengguna juga sering tidak memahami:

- bagian mana dari pesan yang mencurigakan;
- teknik manipulasi apa yang sedang digunakan;
- mengapa teknik tersebut efektif;
- informasi atau tindakan apa yang sebenarnya sedang diminta;
- bagaimana membedakan sinyal risiko dari sekadar bahasa promosi biasa.

Banyak alat scam detection berhenti pada output seperti:

`Scam: 92%`

Output seperti itu dapat membantu screening, tetapi tidak selalu membantu pengguna memahami **mekanisme manipulasi** di balik pesan tersebut.

Scam Museum ingin mengubah proses deteksi menjadi proses inspeksi.

---

## 2. Core Problem Statement

> Bagaimana membantu pengguna mengenali dan memahami pola manipulasi dalam pesan mencurigakan, bukan hanya menerima verdict bahwa pesan tersebut kemungkinan scam?

Produk harus dapat menerima satu pesan, memperkirakan scam risk menggunakan machine learning, lalu menunjukkan evidence yang dapat diperiksa pengguna.

---

## 3. Target User

### Primary user

Pengguna internet yang menerima pesan mencurigakan melalui:

- messaging apps;
- SMS;
- email;
- direct message;
- platform komunikasi digital lainnya.

Primary user tidak diasumsikan memiliki pengetahuan cybersecurity atau machine learning.

### Secondary user

Pelajar, mahasiswa, educator, atau pengguna yang ingin mempelajari pola umum social engineering melalui contoh nyata atau sintetis.

---

## 4. User Situation

Contoh situasi:

> Seorang pengguna menerima pesan yang mengatakan bahwa ia memenangkan hadiah atau memperoleh bantuan finansial, tetapi harus segera membuka sebuah link dan memberikan OTP.

Pengguna ingin mengetahui:

1. apakah pesan tersebut menunjukkan karakteristik scam;
2. bagian mana yang menyebabkan risiko;
3. pola manipulasi apa yang digunakan;
4. mengapa pola tersebut patut dicurigai;
5. apa tindakan aman berikutnya.

---

## 5. Existing User Behavior

Ketika menerima pesan mencurigakan, pengguna kemungkinan melakukan salah satu dari berikut:

- mengabaikannya;
- mempercayainya;
- bertanya kepada teman atau keluarga;
- mencari potongan pesan di mesin pencari;
- memeriksa nomor atau link secara manual;
- memasukkannya ke chatbot atau scam checker;
- baru menyadari scam setelah berinteraksi dengannya.

Problem Brief ini belum memiliki bukti bahwa satu perilaku tertentu merupakan yang paling dominan.

Hal tersebut dianggap sebagai **validation debt**, bukan fakta.

---

## 6. Product Opportunity

Alih-alih menampilkan scam sebagai sekadar kelas prediksi, Scam Museum memperlakukannya sebagai sebuah **digital artifact**.

Setiap pesan dianalisis menjadi sebuah exhibit yang memiliki:

- scam-risk classification;
- manipulation signals;
- suspicious text fragments;
- explanation;
- exhibit title;
- museum-style metadata.

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

Museum metaphor digunakan untuk membuat mekanisme scam lebih mudah diperiksa dan diingat.

Museum bukan pengganti analisis teknis.

Museum adalah cara menyajikan hasil analisis tersebut.

---

## 7. Product Thesis

> **Every scam leaves artifacts.**

Pesan manipulatif meninggalkan pola linguistik dan behavioral signals yang dapat dianalisis.

Machine learning dapat membantu mengenali pola keseluruhan pesan.

Deterministic evidence extraction dapat membantu menunjukkan alasan yang lebih konkret.

Menggabungkan keduanya dapat menghasilkan pengalaman yang lebih informatif daripada verdict tanpa explanation.

---

## 8. Proposed Core Interaction

```text
User pastes suspicious message
            ↓
Text validation
            ↓
Text normalization
            ↓
ML scam-risk classification
            ↓
Manipulation-signal detection
            ↓
Evidence extraction
            ↓
Museum exhibit generation
            ↓
User inspects result
```

Satu input.

Satu analysis action.

Satu hasil utama.

Tidak ada dashboard kompleks.

---

## 9. Proposed AI / ML Role

### Primary ML task

Binary text classification:

```text
SCAM
LEGITIMATE
```

Model menghasilkan scam-risk score atau classification confidence.

### Candidate implementation

```text
Text normalization
        ↓
TF-IDF
        ↓
Logistic Regression
```

Model final belum dikunci sebelum benchmark dilakukan.

Logistic Regression dipilih sebagai kandidat awal karena:

- ringan;
- inference cepat;
- cocok untuk sparse text features;
- mudah direproduksi;
- relatif mudah diinterpretasikan;
- realistis untuk hackathon dengan waktu sangat terbatas.

### Tasks that should remain deterministic

ML tidak perlu menentukan seluruh explanation.

Rule/evidence layer dapat mendeteksi sinyal seperti:

```text
OTP / password request
urgency language
reward bait
suspicious URL pattern
authority impersonation indicators
credential requests
financial requests
```

Ini menjaga explanation tetap inspectable.

---

## 10. Key Differentiator

Scam Museum **bukan hanya scam classifier**.

Diferensiasinya adalah:

> **classification → evidence → educational exhibit**

Produk tidak berhenti pada:

`HIGH RISK`

Tetapi mencoba menjawab:

> **Why does this message look suspicious?**

dan

> **What manipulation pattern is being used?**

Museum interaction menjadi interface utama untuk explanation tersebut.

---

## 11. MVP Scope

### P0 — Must Have

1. Paste suspicious text.
2. Validate input.
3. Run trained ML classifier.
4. Produce scam / legitimate result.
5. Produce risk/confidence score.
6. Detect interpretable scam signals.
7. Highlight or quote suspicious fragments.
8. Generate museum-style exhibit.
9. Display plain-language explanation.
10. Provide several curated sample messages.
11. Responsive web interface.
12. Model evaluation.
13. Basic regression / inference tests.
14. Public GitHub repository.
15. Live deployment.

### P1 — Only If P0 Is Stable

- screenshot upload;
- OCR;
- shareable exhibit image;
- additional scam taxonomy;
- additional visualization.

---

## 12. Explicit Non-Goals

Scam Museum v1 does **not** attempt to become:

- a messaging platform;
- a WhatsApp bot;
- a browser extension;
- an antivirus product;
- a URL reputation service;
- a crowdsourced scam database;
- a real-time threat-intelligence platform;
- an identity-verification service;
- a fact-checking platform;
- an autonomous reporting system;
- a generic AI chatbot;
- a multilingual universal fraud detector;
- a definitive authority determining whether a message is fraudulent.

No user account, history system, or database is required for the hackathon MVP.

---

## 13. Claim Boundary

Scam Museum must not state:

> “This message is definitely a scam.”

A machine-learning model can generate false positives and false negatives.

Preferred framing:

```text
LOW RISK
SUSPICIOUS
HIGH RISK
```

or:

```text
The message contains multiple signals commonly associated with scams.
```

The product is an **educational risk-screening tool**, not proof of criminal activity.

---

## 14. Safety Boundary

Scam Museum should:

- avoid opening suspicious URLs automatically;
- never ask users to submit passwords, OTPs, or credentials;
- treat credential-like input conservatively;
- avoid displaying real personal information in curated examples;
- use synthetic or sanitized example messages;
- avoid encouraging users to interact with suspicious senders.

---

## 15. Success Criteria

MVP dianggap berhasil jika:

### Product

- user dapat memasukkan pesan dan menerima satu exhibit;
- result dapat dipahami tanpa membaca dokumentasi teknis;
- suspicious evidence terlihat jelas;
- UI museum metaphor tetap konsisten.

### ML

- terdapat dataset dan split policy yang terdokumentasi;
- terdapat baseline;
- model dievaluasi pada holdout data;
- metrik utama dilaporkan secara transparan;
- tidak ada data leakage yang diketahui;
- inference reproducible.

### Engineering

- aplikasi dapat dijalankan dari repository;
- model artifact dapat dimuat dengan konsisten;
- failure input ditangani dengan jelas;
- deployed application dapat digunakan tanpa setup lokal.

### Hackathon

Submission harus menunjukkan kekuatan pada:

- **Technical Execution**
- **Innovation & Creativity**
- **User Interface and Design**

---

## 16. Evidence Needed Before Model Lock

Sebelum model dianggap final, kita perlu menentukan:

1. dataset scam/legitimate yang akan digunakan;
2. license dan provenance dataset;
3. apakah dataset cukup relevan dengan message-style scam;
4. class balance;
5. duplicate / near-duplicate risk;
6. train/test split strategy;
7. baseline model;
8. evaluation metric utama;
9. failure cases;
10. apakah probabilities cukup reliable untuk ditampilkan sebagai angka.

Tidak satu pun dari hal tersebut boleh diasumsikan sudah bagus sebelum diuji.

---

## 17. Current Assumptions

### Reasonably supported

- Scam/social-engineering messages memiliki recurring linguistic patterns.
- Text classification adalah task yang cocok untuk ML.
- Lightweight text models memungkinkan development cepat dan reproducible.
- Evidence highlighting berpotensi membuat result lebih interpretable daripada binary verdict saja.

### Still assumptions

- Pengguna akan merasa museum metaphor membantu pembelajaran.
- Dataset yang tersedia cukup representatif untuk target message domain.
- Risk score yang dihasilkan model cukup stabil untuk ditampilkan.
- Manipulation taxonomy dapat dideteksi dengan rule sederhana tanpa terlalu banyak false positives.

Semua poin pada bagian kedua harus diuji atau ditulis sebagai limitation.

---

## 18. Primary Risks

### Risk 1 — Dataset tidak cocok

Dataset spam umum dapat berbeda jauh dari phishing/social-engineering messages yang ingin ditampilkan produk.

**Mitigation:** audit dataset sebelum training dan batasi claim domain.

### Risk 2 — Model terlalu sederhana

Model ringan mungkin kesulitan menangkap konteks scam yang kompleks.

**Mitigation:** benchmark terlebih dahulu. Complexity hanya ditambah bila evidence membenarkan.

### Risk 3 — Museum concept menutupi ML lemah

UI dapat terlihat menarik sementara classification sebenarnya buruk.

**Mitigation:** evaluation metrics dan test cases harus menjadi bagian first-class dari repository.

### Risk 4 — Explanation tidak berasal dari model

Rule-based evidence dapat disalahartikan sebagai penjelasan langsung atas prediction.

**Mitigation:** bedakan secara eksplisit:

```text
ML prediction
Detected evidence signals
```

Jangan menyebut rule signal sebagai causal explanation model.

### Risk 5 — False confidence

Angka seperti `92% scam` dapat terlihat lebih pasti daripada kualitas model sebenarnya.

**Mitigation:** evaluasi calibration atau gunakan categorical risk bands bila probability tidak cukup terpercaya.

---

## 19. Validation Debt

Belum tersedia:

- user interview;
- usability test;
- field validation;
- evidence bahwa museum framing meningkatkan scam awareness;
- final dataset audit;
- final benchmark;
- final model selection;
- deployed-system performance measurement.

Hackathon submission tidak boleh mengubah validation debt tersebut menjadi klaim seolah sudah terbukti.

---

## 20. Scope Decision

Scam Museum akan dibangun sebagai:

> **A small, explainable ML-powered web experience for examining suspicious messages as museum artifacts of digital manipulation.**

Fokus utama:

```text
ONE MESSAGE
ONE CLASSIFICATION
VISIBLE EVIDENCE
ONE MEMORABLE EXHIBIT
```

Bukan platform cybersecurity lengkap.

---

## 21. Problem Brief Gate

| Question | Status |
|---|---|
| Problem cukup jelas? | PASS |
| Primary user jelas? | PASS |
| AI/ML relevan? | PASS |
| Core interaction dapat dijelaskan singkat? | PASS |
| Differentiation jelas? | PASS |
| Scope realistis untuk 1–2 hari? | PASS |
| Non-goals cukup keras? | PASS |
| Claim boundary ada? | PASS |
| Dataset telah dipilih dan diaudit? | PENDING |
| Model telah dibenchmark? | PENDING |
| Evaluation contract telah dikunci? | PENDING |

### Gate Decision

**PASS TO DATASET & EVALUATION DESIGN**

Coding production belum perlu dimulai sebelum dataset candidate dan evaluation contract minimal dikunci.
