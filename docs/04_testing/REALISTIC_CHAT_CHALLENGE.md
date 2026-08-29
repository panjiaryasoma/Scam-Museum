# Realistic Chat Challenge Pack v0.1

Synthetic test-only messages that look closer to pasted WhatsApp/iMessage/DM text:
slang, typos, emoji, short exchanges, speaker labels, and hard negatives.

`review_target` is intentionally NOT a locked regression verdict yet.
Run the frozen v0.5 model first, inspect mismatches, then promote defensible
cases into strict fixtures.

## Run

```powershell
uv run pytest -v tests/test_realistic_chat_http.py
uv run pytest -q
uv run python scripts/audit_realistic_chats.py
```

From the current 123-test baseline, 24 new HTTP robustness cases produce
147 total tests.

Audit output:

```text
reports/realistic_chat_v05_audit.json
```

## Sample manual pastes

Family scam:
```text
mum its me 😭 smashed my phone so this is my temp number. can u send £420 to this account today? i'll pay u back tomorrow x
```

Pasted chat:
```text
Boss: hey are you free?
You: yep what's up
Boss: stuck in a client meeting. need 5 apple gift cards for the team
Boss: £100 each. buy them now and send me pics of the codes
```

Hard negative:
```text
Alex: got the concert tickets
You: niceee
Alex: your half was £42 btw
You: sending it now
```

Ambiguous:
```text
Unknown: hey anna, still on for coffee tomorrow?
You: wrong number sorry
Unknown: oh wow my bad 😅 hope i didn't bother you
```

Do not rewrite `review_target` just to improve the match rate. Review first.
