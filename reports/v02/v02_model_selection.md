# Scam Museum — v0.2 Model Selection

Selected model: **char_lr_v02**

| Model | CV F1-macro | Temporal recall | Selection score |
|---|---:|---:|---:|
| char_lr_v02 | 0.9810 | 0.9474 | 0.9639 |
| word_char_lr_v02 | 0.9800 | 0.9474 | 0.9634 |
| word_lr_v02 | 0.9681 | 0.9474 | 0.9576 |

## Original primary locked test

- F1-macro: `0.9807`
- Scam precision: `0.9333`
- Scam recall: `1.0000`
- Scam F1: `0.9655`
- Average precision: `0.9729`

This locked test was not used in model selection.
