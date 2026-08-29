# Scam Museum — Manual UI Acceptance Tests v0.1

Purpose: verify the actual browser interaction used by judges and users.

These are **acceptance fixtures**, not training data and not claims about
real-world scam prevalence.

## Preconditions

Start the application:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

For every case:

1. Paste the exact message into **Paste a suspicious message**.
2. Click **Analyze artifact**.
3. Confirm the expected verdict.
4. Confirm the original text appears in **Submitted artifact**.
5. Confirm the page renders observed artifacts without a JavaScript error.
6. Use **Examine another message** before the next case.

---

## Case M01 — High Risk / OTP phishing

Input:

```text
Your account will be suspended immediately. Send us your OTP to verify your account.
```

Expected:

```text
HIGH RISK
```

Expected visible evidence includes:

```text
Account threat
Time urgency
OTP request
```

---

## Case M02 — High Risk / shortened URL

Input:

```text
Your account is locked. Verify immediately at https://bit.ly/secure-now
```

Expected:

```text
HIGH RISK
```

Expected visible evidence includes:

```text
Account threat
Time urgency
Suspicious URL
```

---

## Case M03 — High Risk / family impersonation

Input:

```text
Hi Mum, this is my new number. Please send £900 today.
```

Expected:

```text
HIGH RISK
```

Expected visible evidence includes:

```text
Family impersonation
New number claim
Money transfer request
```

---

## Case M04 — Suspicious / request without enough supporting context

Input:

```text
Send us your OTP.
```

Expected:

```text
SUSPICIOUS
```

The system should not silently promote every single OTP-related phrase to
HIGH RISK.

---

## Case M05 — Low Risk / protective OTP language

Input:

```text
Your OTP is 482193. Do not share your OTP with anyone.
```

Expected:

```text
LOW RISK
```

Expected protective evidence:

```text
Do-not-share warning
```

Must **not** be presented as an OTP request.

---

## Case M06 — Low Risk / ordinary conversation

Input:

```text
Dinner is at seven. See you at home.
```

Expected:

```text
LOW RISK
```

No material scam evidence should be shown.

---

## Case M07 — Low Risk / ordinary URL

Input:

```text
Your parcel has shipped. Track it at https://amazon.com/orders
```

Expected:

```text
LOW RISK
```

The normal URL must not automatically become **Suspicious URL**.

---

## Case M08 — Insufficient Evidence / wrong-number opener

Input:

```text
Hi, is this Sarah?
```

Expected:

```text
INSUFFICIENT EVIDENCE
```

The museum may surface **Unexpected contact**, but should abstain from
calling the message a scam.

---

## Case M09 — Insufficient Evidence / new-number opener

Input:

```text
Hi Mum, this is my new number.
```

Expected:

```text
INSUFFICIENT EVIDENCE
```

Family/new-number patterns may be visible, but there is no request, payment,
credential demand, or threat yet.

---

## Case M10 — Empty input validation

Leave the textarea empty and click **Analyze artifact**.

Expected:

```text
No request is sent.
A visible validation error asks for a message.
```

---

## Case M11 — Keyboard submission

Paste M01 and press:

```text
Ctrl + Enter
```

Expected:

```text
Same result as clicking Analyze artifact.
```

---

## Case M12 — Maximum length

The textarea must stop accepting input after:

```text
5000 characters
```

The server independently rejects payloads over 5000 characters.

---

## Automated companion test

The browser's manual form sends the same HTTP request covered by:

```powershell
uv run pytest -v tests/test_manual_entry_http.py
```

It checks nine representative messages through the **real FastAPI
`POST /api/analyze` route using the frozen v0.5 model**, plus blank and
oversized request rejection.

After adding it, the current 112-test suite should become:

```text
123 passed
```

assuming no other tests were added.

Then run:

```powershell
uv run pytest -q
```

Do not edit expected verdicts just to make a failure green. A failure here
means either the browser/API contract changed or the frozen behavior no
longer matches the accepted fixture.
