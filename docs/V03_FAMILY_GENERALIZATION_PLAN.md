# Scam Museum — v0.3 Family-Generalization Plan

## Reason for the change

The prepared IMC25 English challenge contains 14,362 unique messages, but only 74 rows have a usable timestamp. A temporal split is therefore not statistically useful.

v0.3 replaces temporal evaluation with **leave-one-scam-family-out (LOFO)** evaluation.

For every scam family:

1. hold that family out completely;
2. train on the original primary development set plus the other IMC25 scam families;
3. evaluate recall on the held-out family;
4. repeat for every family.

This directly tests robustness to scam styles the model was not trained on.

## Data roles

- Mishra & Soni primary development: in-domain grouped CV and negative examples.
- Mishra & Soni original locked test: untouched until model selection.
- IMC25 English non-spam: modern positive development data and LOFO family challenges.
- Financial Scams Detection Dataset v2 (2025): final independent English scam+ham benchmark, never used for tuning.

## Training controls

- Maximum 5 rows per normalized IMC25 template.
- Maximum 2,000 rows per scam family.
- Conflicting normalized templates assigned to multiple scam families are removed from LOFO evaluation.
- No synthetic training data.

## Selection

For each model:

- Primary grouped-CV F1-macro.
- Equal-weight macro recall across held-out scam families.
- Weighted recall across all held-out messages.

Selection score:

`harmonic_mean(primary_cv_f1_macro, family_macro_recall)`

A candidate must keep primary grouped-CV F1-macro >= 0.95.

## Claim boundary

Allowed:

> Evaluated for generalization to held-out scam families and an independent cross-dataset benchmark.

Not allowed:

> Predicts future scams.
