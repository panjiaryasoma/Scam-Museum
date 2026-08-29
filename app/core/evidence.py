from __future__ import annotations

import ipaddress
import re
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Evidence:
    id: str
    category: str
    strength: str
    matched_text: str
    start: int
    end: int
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


REQUEST_VERBS = r"(?:send|share|provide|enter|submit|confirm|give|reply\s+with|tell\s+me|verify\s+with)"
MONEY_VERBS = r"(?:send|transfer|wire|pay|deposit|remit)"
CONTACT_VERBS = r"(?:reply|call|contact|text|message|whatsapp)"

RULES = [
    (
        "OTP_REQUEST", "operational", "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,45}}\b(?:otp|one[- ]time password|security code|verification code|passcode)\b"
        rf"|\b(?:otp|one[- ]time password|security code|verification code|passcode)\b.{{0,45}}\b{REQUEST_VERBS}\b",
        "Requests disclosure or submission of an OTP/security code.",
    ),
    (
        "CREDENTIAL_REQUEST", "operational", "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,45}}\b(?:password|pin|cvv|login credentials?|passcode)\b"
        rf"|\b(?:password|pin|cvv|login credentials?|passcode)\b.{{0,45}}\b{REQUEST_VERBS}\b",
        "Requests authentication secrets or credentials.",
    ),
    (
        "FINANCIAL_INFO_REQUEST", "operational", "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,55}}\b(?:bank account|account number|card number|debit card|credit card|routing number|iban|cvv)\b"
        rf"|\b(?:bank account|account number|card number|debit card|credit card|routing number|iban|cvv)\b.{{0,55}}\b{REQUEST_VERBS}\b",
        "Requests financial account or card information.",
    ),
    (
        "MONEY_TRANSFER_REQUEST", "operational", "critical",
        rf"\b{MONEY_VERBS}\b.{{0,35}}\b(?:money|funds?|cash|\$|£|€|usd|gbp|eur|\d{{2,}})\b"
        rf"|\b(?:money|funds?|cash|\$|£|€|usd|gbp|eur)\b.{{0,35}}\b{MONEY_VERBS}\b",
        "Requests a money transfer or movement of funds.",
    ),
    (
        "PAYMENT_REQUEST", "operational", "strong",
        r"\b(?:pay|payment|fee|deposit|settlement|charge)\b.{0,35}\b(?:now|today|required|due|release|receive|claim|process)\b"
        r"|\b(?:processing fee|delivery fee|release fee|verification fee)\b",
        "Requests or conditions an action on a payment or fee.",
    ),
    (
        "TIME_URGENCY", "manipulation", "supporting",
        r"\b(?:urgent|urgently|immediately|right now|act now|today only|within \d+ (?:minutes?|hours?)|expires? today|final warning|as soon as possible|asap)\b",
        "Creates immediate time pressure.",
    ),
    (
        "ACCOUNT_THREAT", "manipulation", "strong",
        r"\b(?:account|profile|card|service)\b.{0,35}\b(?:suspend(?:ed)?|block(?:ed)?|lock(?:ed)?|close(?:d)?|disable(?:d)?|terminate(?:d)?|restricted?)\b"
        r"|\b(?:suspend(?:ed)?|block(?:ed)?|lock(?:ed)?|close(?:d)?|disable(?:d)?|terminate(?:d)?|restricted?)\b.{0,35}\b(?:account|profile|card|service)\b",
        "Threatens account or service restriction.",
    ),
    (
        "AUTHORITY_CLAIM", "manipulation", "supporting",
        r"\b(?:bank|police|government|tax office|revenue service|customs|support team|security team|delivery service|courier)\b",
        "Invokes an institution or authority role.",
    ),
    (
        "NEED_AND_GREED", "manipulation", "supporting",
        r"\b(?:winner|won|prize|reward|refund|cashback|compensation|loan approved|approved loan|gift card|bonus)\b",
        "Uses an unexpected benefit, reward, refund, or approval lure.",
    ),
    (
        "FAMILY_IMPERSONATION", "contextual", "supporting",
        r"\b(?:mum|mom|mummy|mother|dad|daddy|father|son|daughter|brother|sister)\b",
        "Frames the sender as a close family member.",
    ),
    (
        "NEW_NUMBER_CLAIM", "contextual", "supporting",
        r"\b(?:my new number|new phone number|changed my number|lost my phone|new phone|new sim)\b",
        "Claims a new or changed phone number.",
    ),
    (
        "UNEXPECTED_CONTACT", "contextual", "weak",
        r"(?:\bis this [a-z][a-z .'-]{1,30}\?|\bwrong number\b|\bsorry,? wrong number\b|\bfound your number\b|\bdo i know you\b)",
        "Opens as an unexpected or wrong-number contact.",
    ),
    (
        "REPLY_OR_CALL_REQUEST", "operational", "supporting",
        rf"\b{CONTACT_VERBS}\b.{{0,30}}\b(?:me|us|this number|immediately|now|back)\b",
        "Requests direct contact or continuation.",
    ),
]

PROTECTIVE_RULES = [
    (
        "PROTECTIVE_DO_NOT_SHARE",
        r"\b(?:do not|don't|never)\s+(?:share|send|give|provide)\b.{0,45}\b(?:otp|password|pin|cvv|security code|verification code|passcode)\b"
        r"|\b(?:otp|password|pin|cvv|security code|verification code|passcode)\b.{0,45}\b(?:do not|don't|never)\s+(?:share|send|give|provide)\b",
        "Explicitly advises the recipient not to disclose a secret.",
    ),
    (
        "ANTI_SCAM_ADVICE",
        r"\b(?:ignore unknown sms|ignore suspicious messages?|report fraud|beware of scams?|do not click suspicious links?|never share your credentials?|we will never ask for your password|we will never ask for your otp)\b",
        "Contains anti-fraud or protective guidance.",
    ),
]

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>()]+")
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "cutt.ly", "rb.gy", "rebrand.ly", "shorturl.at",
}
BAIT_HOST_TERMS = {
    "secure", "verify", "verification", "login", "account",
    "update", "support", "wallet", "banking", "recover",
}


def _is_suspicious_url(raw: str) -> tuple[bool, str]:
    candidate = raw.rstrip(".,;:!?)]}")
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = (parsed.hostname or "").lower()

    if not host:
        return True, "URL host could not be parsed reliably."

    if host in SHORTENERS or any(host.endswith("." + d) for d in SHORTENERS):
        return True, "Uses a known URL-shortening host."

    if "xn--" in host:
        return True, "Uses punycode in the host."

    try:
        ipaddress.ip_address(host)
        return True, "Uses a raw IP address as the host."
    except ValueError:
        pass

    host_tokens = set(re.split(r"[-._]", host))
    if len(host_tokens & BAIT_HOST_TERMS) >= 2:
        return True, "Host contains multiple account/credential bait terms."

    return False, ""


def detect_evidence(text: str) -> tuple[list[Evidence], list[Evidence]]:
    positive: list[Evidence] = []
    protective: list[Evidence] = []
    seen: set[tuple[str, int, int]] = set()

    request_ids = {
        "OTP_REQUEST",
        "CREDENTIAL_REQUEST",
        "FINANCIAL_INFO_REQUEST",
    }

    for evidence_id, category, strength, pattern, rationale in RULES:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            # "Do not share your OTP" is protective advice, not an OTP request.
            # Check the immediate prefix because the positive regex begins at
            # the request verb and therefore does not include the negator.
            if evidence_id in request_ids:
                prefix = text[max(0, match.start() - 20):match.start()]
                matched_lower = match.group(0).lower()
                negated_inside = re.search(
                    r"(?:do not|don't|never)\s+"
                    r"(?:share|send|give|provide|enter|submit|confirm)",
                    matched_lower,
                    flags=re.IGNORECASE,
                )
                negated_prefix = re.search(
                    r"(?:do not|don't|never)\s*$",
                    prefix,
                    flags=re.IGNORECASE,
                )
                if negated_inside or negated_prefix:
                    continue

            key = (evidence_id, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            positive.append(Evidence(
                evidence_id, category, strength, match.group(0),
                match.start(), match.end(), rationale
            ))

    for match in URL_RE.finditer(text):
        suspicious, rationale = _is_suspicious_url(match.group(0))
        if suspicious:
            positive.append(Evidence(
                "SUSPICIOUS_URL", "operational", "strong",
                match.group(0), match.start(), match.end(), rationale
            ))

    for evidence_id, pattern, rationale in PROTECTIVE_RULES:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            protective.append(Evidence(
                evidence_id, "protective", "protective",
                match.group(0), match.start(), match.end(), rationale
            ))

    positive.sort(key=lambda x: (x.start, x.end, x.id))
    protective.sort(key=lambda x: (x.start, x.end, x.id))
    return positive, protective
