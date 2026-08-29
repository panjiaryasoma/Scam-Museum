# Realistic Chat Hardening v0.1

## Why this patch exists

The frozen v0.5 model is not retrained.

A 24-case realistic-chat diagnostic produced:

```text
15 / 24 review-target matches
62.5% diagnostic agreement
```

This is NOT model accuracy. The review targets are human expectations on a
synthetic challenge set.

Nine mismatches were inspected.

## Mismatch disposition

### Fix: RC02

Family/new-number scam contained:

```text
need £650 ... can you transfer it now?
```

The previous money regex handled a transfer verb before the amount more
reliably than an amount before the transfer verb.

Fix: broaden `MONEY_TRANSFER_REQUEST`.

### Fix: RC03

The message requested:

```text
the 6 digit code we just texted you
```

The previous OTP rule required terms such as `OTP`, `security code`, or
`verification code`.

Fix: recognize `6 digit code`, `6-digit code`, and `six digit code`.

### Fix: RC04

Delivery message combined:

```text
payment/fee request
shortened URL
deadline
```

Fix:
- recognize `before 6pm` as urgency;
- promote `PAYMENT_REQUEST + SUSPICIOUS_URL + TIME_URGENCY` to HIGH RISK.

### Fix: RC05

Gift-card boss impersonation was invisible to the operational detector.

Fix:
- add a narrow `GIFT_CARD_REQUEST` rule that requires gift cards plus code
  disclosure language;
- recognize action phrases such as `buy them now`.

### Keep model frozen: RC07

The remote-job message has an ELEVATED ML signal but no currently accepted
deterministic evidence.

It remains LOW RISK under the existing philosophy:

```text
ML is a signal, not the verdict.
```

Do not change the policy merely to make the synthetic audit reach 100%.

This remains a documented limitation / future evidence-taxonomy candidate.

### Fix: RC08

Crypto recovery advance-fee scam contained a recovery lure plus a fee that
must be paid first.

Fix:
- expand `NEED_AND_GREED` to recovery lures;
- expand `PAYMENT_REQUEST` to `fee ... paying first`;
- promote `NEED_AND_GREED + PAYMENT_REQUEST` to HIGH RISK.

### Fix: RC10

The account takeover message used:

```text
closed in 30 minutes
```

The old urgency regex only understood `within 30 minutes`.

Fix: support `in N minutes/hours`.

### Fix: RC17

A legitimate dinner repayment was marked suspicious because any
`MONEY_TRANSFER_REQUEST` was considered critical.

Fix:
- money movement remains observable evidence;
- reclassify it from critical to strong;
- family/new-number + money remains explicitly HIGH RISK.

This preserves the useful family-scam rule without pretending every Venmo
request is fraud.

### Fix: RC18

`wifi password` was classified as an account credential.

Fix: exclude Wi-Fi, wireless, and network passwords from
`CREDENTIAL_REQUEST`.

## Expected post-patch diagnostic

If the new rules behave as intended, eight of the nine current mismatches
should resolve.

The expected realistic-chat diagnostic becomes approximately:

```text
23 / 24 review-target matches
95.8% diagnostic agreement
```

RC07 is expected to remain a deliberate mismatch.

This number is still NOT an accuracy claim.

## Run order

```powershell
uv run pytest -v tests/test_evidence.py tests/test_risk.py
uv run pytest -q
uv run python -m scripts.audit_realistic_chats
```

The current 147-test suite receives 17 additional regression cases, so the
expected total is:

```text
164 passed
```

Then inspect:

```powershell
$d = Get-Content reports/realistic_chat_v05_audit.json -Raw -Encoding UTF8 |
  ConvertFrom-Json

$d.results |
  Where-Object { -not $_.target_match } |
  ForEach-Object {
    "{0}: {1} -> {2} | ML={3} {4:N3} | evidence={5}" -f `
      $_.id, `
      $_.review_target, `
      $_.actual_verdict, `
      $_.ml_signal.label, `
      $_.ml_signal.score, `
      (($_.evidence_ids) -join ",")
  }
```

Do not commit until both the full pytest suite and the rerun diagnostic have
been reviewed.
