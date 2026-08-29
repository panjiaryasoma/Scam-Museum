# Scam Museum — Evidence & Decision Contract

**Version:** 0.1
**Status:** Locked for P0 implementation

## 1. Purpose

Scam Museum must not use the frozen v0.5 classifier as the final scam/legitimate judge.

The final decision combines:

1. ML text-risk signal;
2. observable message evidence;
3. protective/counter-evidence;
4. explicit uncertainty.

The system analyzes only the supplied message text. It does not verify sender identity, domain ownership, account status, or real-world intent.

## 2. Final verdicts

Only these P0 verdicts are allowed:

```text
LOW RISK
SUSPICIOUS
HIGH RISK
INSUFFICIENT EVIDENCE
```

`LOW RISK` means no material scam request was detected. It is not a guarantee that the sender is safe.

`SUSPICIOUS` means the message contains meaningful risk signals but not enough observable evidence for a high-risk verdict.

`HIGH RISK` means multiple strong scam behaviors are observable in the message.

`INSUFFICIENT EVIDENCE` is an abstention state for messages that are ambiguous in isolation.

Examples:

```text
Hi, is this Sarah?
Hi Mum, this is my new number.
```

must not be forced into scam/legitimate labels without an actionable request.

## 3. ML risk signal

The runtime reads the frozen model threshold from:

```text
models/scam_classifier_v05_metadata.json
```

The model score is an internal risk score, **not a calibrated probability**.

Signal mapping:

```text
score < 0.50                     -> WEAK
0.50 <= score < model threshold -> ELEVATED
score >= model threshold        -> STRONG
```

The UI may say:

```text
ML Risk Signal: Strong
```

It must not say:

```text
92% chance this is a scam
```

unless calibration is separately validated.

## 4. Evidence taxonomy

### Operational evidence

| ID | Strength | Definition |
|---|---:|---|
| `OTP_REQUEST` | Critical | Requests an OTP/security code |
| `CREDENTIAL_REQUEST` | Critical | Requests password, PIN, CVV, login credentials, or similar secrets |
| `FINANCIAL_INFO_REQUEST` | Critical | Requests bank/card/account details |
| `MONEY_TRANSFER_REQUEST` | Critical | Requests money transfer/wire/send-money behavior |
| `PAYMENT_REQUEST` | Strong | Requests a fee, deposit, payment, or settlement |
| `SUSPICIOUS_URL` | Strong | URL triggers deterministic suspicious-host rules |
| `REPLY_OR_CALL_REQUEST` | Supporting | Explicitly requests reply/call/contact |

### Threat/manipulation evidence

| ID | Strength | Definition |
|---|---:|---|
| `TIME_URGENCY` | Supporting | Creates immediate time pressure |
| `ACCOUNT_THREAT` | Strong | Threatens account/service suspension, blocking, closure, or restriction |
| `AUTHORITY_CLAIM` | Supporting | Invokes bank, government, police, tax, security, support, courier, etc. |
| `NEED_AND_GREED` | Supporting | Prize, reward, refund, loan, compensation, bonus, or similar lure |

### Contextual evidence

Contextual evidence is weak in isolation.

| ID | Strength | Definition |
|---|---:|---|
| `FAMILY_IMPERSONATION` | Supporting | Presents sender as close family |
| `NEW_NUMBER_CLAIM` | Supporting | Claims a changed/new phone number |
| `UNEXPECTED_CONTACT` | Weak | Wrong-number or unexpected-contact opening |

### Protective evidence

| ID | Definition |
|---|---|
| `PROTECTIVE_DO_NOT_SHARE` | Tells recipient not to share OTP/password/PIN/security code |
| `ANTI_SCAM_ADVICE` | Warns against fraud, suspicious links, unknown messages, or credential sharing |

Protective evidence may reduce risk only when no critical or strong positive evidence exists.

A malicious request always outranks protective wording.

## 5. URL rules

P0 performs no live URL reputation lookup.

`SUSPICIOUS_URL` may trigger for deterministic indicators such as:

- known URL shortener;
- raw IP host;
- punycode host;
- multiple credential/account bait terms in the host.

A URL is not suspicious merely because one exists.

## 6. Decision precedence

### A. HIGH RISK

Return `HIGH RISK` when any condition is true:

1. two or more critical evidence IDs are present;
2. one critical evidence ID plus another meaningful positive evidence ID is present;
3. `SUSPICIOUS_URL + ACCOUNT_THREAT + TIME_URGENCY` are present;
4. `MONEY_TRANSFER_REQUEST` appears with `FAMILY_IMPERSONATION` or `NEW_NUMBER_CLAIM`.

### B. Protective LOW RISK

Return `LOW RISK` when protective evidence exists and no critical or strong positive evidence exists.

### C. SUSPICIOUS

Return `SUSPICIOUS` when:

1. exactly one critical request exists without enough support for `HIGH RISK`;
2. two or more non-weak positive evidence items exist;
3. ML signal is `STRONG` and observable evidence exists;
4. ML signal is `STRONG` but deterministic evidence is limited.

ML alone may raise the verdict to `SUSPICIOUS`, never directly to `HIGH RISK`.

### D. INSUFFICIENT EVIDENCE

Return `INSUFFICIENT EVIDENCE` when only ambiguous contextual/opening evidence exists.

Examples:

```text
Hi, is this Sarah?
Hi Mum, this is my new number.
```

### E. LOW RISK

Return `LOW RISK` when no critical/strong risk evidence exists, no ambiguity rule applies, and no contradictory suspicious combination is present.

## 7. Output contract

```json
{
  "verdict": "SUSPICIOUS",
  "ml_signal": {
    "label": "STRONG",
    "score": 0.81,
    "model_version": "0.5",
    "threshold": 0.8
  },
  "evidence": [],
  "protective_evidence": [],
  "reason_codes": []
}
```

Evidence items include:

```text
id
category
strength
matched_text
start
end
rationale
```

Text spans exist so the UI can highlight observable artifacts.

## 8. Locked P0 behaviors

| Pattern | Expected behavior |
|---|---|
| Legit OTP notification + “do not share” | `LOW RISK` |
| Explicit OTP request + threat/urgency | `HIGH RISK` |
| Legit delivery update with ordinary URL | not automatically `HIGH RISK` |
| Account threat + suspicious URL + urgency | `HIGH RISK` |
| Bank security notification without request | not automatically `HIGH RISK` |
| Account threat + credential request | `HIGH RISK` |
| “Hi, is this Sarah?” | `INSUFFICIENT EVIDENCE` |
| “Hi Mum, this is my new number.” | `INSUFFICIENT EVIDENCE` |
| Family/new-number claim + money transfer | `HIGH RISK` |
| Plain harmless conversation | `LOW RISK` |

## 9. Claims boundary

Allowed:

> Scam Museum screens supplied message text for scam-related risk patterns and observable manipulation/evidence signals.

Not allowed:

> Scam Museum verifies whether a sender is a scammer.

Not allowed:

> Scam Museum detects all scams.

The project should disclose that cross-dataset domain shift was observed and that some scams are inherently ambiguous from a single message.

## 10. P0 non-goals

Not included:

- OCR;
- image analysis;
- sender verification;
- live URL reputation;
- browser extension;
- thread-level conversation analysis;
- LLM-generated explanations;
- automatic blocking;
- multilingual guarantees.
