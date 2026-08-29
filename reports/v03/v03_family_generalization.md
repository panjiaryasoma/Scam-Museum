# Scam Museum — v0.3 Family Generalization

Selected model: **word_char_lr_v03**

| Model | Primary CV F1 | Family macro recall | Weighted recall | Selection score |
|---|---:|---:|---:|---:|
| word_lr_v03 | 0.9763 | 0.8426 | 0.9546 | 0.9045 |
| char_lr_v03 | 0.9864 | 0.8723 | 0.9572 | 0.9258 |
| word_char_lr_v03 | 0.9847 | 0.8805 | 0.9628 | 0.9297 |

## Selected model: held-out family recall

| Family | n | Templates | Recall |
|---|---:|---:|---:|
| banking | 6,441 | 6,367 | 0.9964 |
| delivery | 1,236 | 1,231 | 0.9733 |
| government | 1,331 | 1,331 | 0.9797 |
| hey mum/dad | 55 | 55 | 0.7091 |
| others | 3,691 | 3,678 | 0.9087 |
| telecom | 1,379 | 1,376 | 0.9927 |
| wrong number | 222 | 222 | 0.6036 |

## Original primary locked test

- F1-macro: `0.9690`
- Scam precision: `0.9024`
- Scam recall: `0.9911`
- Scam F1: `0.9447`
