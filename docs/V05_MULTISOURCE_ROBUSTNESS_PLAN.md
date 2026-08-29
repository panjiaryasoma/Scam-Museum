# SCAM MUSEUM — V0.5 MULTI-SOURCE ROBUSTNESS PLAN

**Version:** 0.5  
**Status:** Final ML Iteration / Ready to Run

## Objective

v0.5 targets the remaining weakness from v0.4: **legitimate-message domain shift**.

Development negatives now come from multiple domains:

- Primary HAM
- Financial English HAM
- SmishX legitimate

Positive diversity remains:

- Primary smishing
- IMC25 modern scam families

## Evaluation

v0.5 selects both model and threshold using three development properties:

1. Primary grouped out-of-fold F1-macro
2. Leave-one-scam-family-out macro recall
3. Leave-one-hard-negative-source-out macro specificity

Threshold candidates:

`0.50, 0.60, 0.70, 0.80, 0.90`

Selection score:

`harmonic_mean(primary_oof_f1, family_macro_recall, negative_source_macro_specificity)`

Eligibility requires primary OOF F1-macro >= 0.94.

## Candidate Models

- word + char TF-IDF + balanced Logistic Regression
- word + char TF-IDF + negative class weight 2:1
- word + char TF-IDF + negative class weight 3:1

## Training Controls

IMC25:

- max 5 rows per normalized template
- max 2000 rows per scam family

Hard-negative sources are normalized and cross-source duplicates are removed. Any hard negative overlapping a known positive template is removed.

## Stop Rule

v0.5 is the last classifier iteration for HackSocial P0.

If the next untouched cross-dataset benchmark still shows poor specificity/balanced accuracy, do not create v0.6. Ship a narrower risk-screening classifier with evidence and abstention instead.
