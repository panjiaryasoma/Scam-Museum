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


REQUEST_VERBS = (
    r"(?:send|share|provide|enter|submit|confirm|give|reply\s+with|"
    r"tell\s+me|verify\s+with)"
)
MONEY_VERBS = r"\b(?:send|transfer|wire|pay|deposit|remit)\b"
CONTACT_VERBS = r"(?:reply|call|contact|text|message|whatsapp)"

CODE_TERMS = (
    r"(?:otp|one[- ]time password|security code|verification code|passcode|"
    r"(?:6|six)[- ]?digit code)"
)

MONEY_TERMS = (
    r"(?:[$£€]\s?\d+(?:[.,]\d+)?|"
    r"\b\d+(?:[.,]\d+)?\s?(?:usd|gbp|eur)\b|"
    r"\b(?:money|funds?|cash|usd|gbp|eur)\b)"
)


RULES = [
    (
        "OTP_REQUEST",
        "operational",
        "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,45}}\b{CODE_TERMS}\b"
        rf"|\b{CODE_TERMS}\b.{{0,45}}\b{REQUEST_VERBS}\b",
        "Requests disclosure or submission of an OTP/security code.",
    ),
    (
        "CREDENTIAL_REQUEST",
        "operational",
        "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,45}}\b"
        rf"(?:password|pin|cvv|login credentials?|passcode)\b"
        rf"|\b(?:password|pin|cvv|login credentials?|passcode)\b"
        rf".{{0,45}}\b{REQUEST_VERBS}\b",
        "Requests authentication secrets or credentials.",
    ),
    (
        "FINANCIAL_INFO_REQUEST",
        "operational",
        "critical",
        rf"\b{REQUEST_VERBS}\b.{{0,55}}\b"
        rf"(?:bank account|account number|card number|card details?|debit card|"
        rf"credit card|routing number|iban|cvv)\b"
        rf"|\b(?:bank account|account number|card number|card details?|debit card|"
        rf"credit card|routing number|iban|cvv)\b"
        rf".{{0,55}}\b{REQUEST_VERBS}\b",
        "Requests financial account or card information.",
    ),
    (
        "GIFT_CARD_REQUEST",
        "operational",
        "critical",
        r"\b(?:need|buy|purchase|get|grab)\b.{0,80}\b"
        r"gift cards?\b.{0,120}\b(?:send|share|text|message)\b"
        r".{0,50}\b(?:codes?|photos?|pics?|pictures?)\b"
        r"|\bgift cards?\b.{0,120}\b(?:send|share|text|message)\b"
        r".{0,50}\b(?:codes?|photos?|pics?|pictures?)\b",
        "Requests transferable gift cards and disclosure of their codes.",
    ),
    (
        "MONEY_TRANSFER_REQUEST",
        "operational",
        "strong",
        rf"{MONEY_VERBS}.{{0,55}}{MONEY_TERMS}"
        rf"|{MONEY_TERMS}.{{0,65}}{MONEY_VERBS}",
        "Requests a money transfer or movement of funds.",
    ),
    (
        "PAYMENT_REQUEST",
        "operational",
        "strong",
        r"\b(?:pay|payment|fee|deposit|settlement|charge)\b.{0,45}\b"
        r"(?:now|today|required|due|release|receive|claim|process|"
        r"pay|paying|paid|first|before|upfront)\b"
        r"|\b(?:processing fee|delivery fee|release fee|verification fee)\b",
        "Requests or conditions an action on a payment or fee.",
    ),
    (
        "TIME_URGENCY",
        "manipulation",
        "supporting",
        r"\b(?:urgent|urgently|immediately|right now|act now|today only|"
        r"within \d+ (?:minutes?|hours?)|in \d+ (?:minutes?|hours?)|"
        r"before \d{1,2}(?::\d{2})?\s*(?:am|pm)|expires? today|"
        r"final warning|as soon as possible|asap)\b"
        r"|\b(?:buy|send|transfer|pay|reply|verify|contact)\b"
        r".{0,20}\bnow\b",
        "Creates immediate time pressure.",
    ),
    (
        "ACCOUNT_THREAT",
        "manipulation",
        "strong",
        r"\b(?:account|profile|card|service)\b.{0,35}\b"
        r"(?:suspend(?:ed)?|block(?:ed)?|lock(?:ed)?|close(?:d)?|"
        r"disable(?:d)?|terminate(?:d)?|restricted?)\b"
        r"|\b(?:suspend(?:ed)?|block(?:ed)?|lock(?:ed)?|close(?:d)?|"
        r"disable(?:d)?|terminate(?:d)?|restricted?)\b.{0,35}\b"
        r"(?:account|profile|card|service)\b",
        "Threatens account or service restriction.",
    ),
    (
        "AUTHORITY_CLAIM",
        "manipulation",
        "supporting",
        r"\b(?:bank|police|government|tax office|revenue service|customs|"
        r"support team|security team|delivery service|courier)\b",
        "Invokes an institution or authority role.",
    ),
    (
        "RECOVERY_LURE",
        "manipulation",
        "supporting",
        r"\b(?:recover(?:ed|y|ing)?|retriev(?:ed|e|ing))\b.{0,45}\b"
        r"(?:crypto|funds?|money|wallet|assets?)\b"
        r"|\b(?:crypto|funds?|money|wallet|assets?)\b.{0,45}\b"
        r"(?:recover(?:ed|y|ing)?|retriev(?:ed|e|ing))\b",
        "Claims recovery of previously lost money, crypto, or assets.",
    ),
    (
        "NEED_AND_GREED",
        "manipulation",
        "supporting",
        r"\b(?:winner|won|prize|reward|refund|cashback|compensation|"
        r"loan approved|approved loan|gift cards?|bonus)\b",
        "Uses an unexpected benefit, reward, refund, or approval lure.",
    ),
    (
        "FAMILY_IMPERSONATION",
        "contextual",
        "supporting",
        r"\b(?:mum|mom|mummy|mother|dad|daddy|father|son|daughter|"
        r"brother|sister)\b",
        "Frames the sender as a close family member.",
    ),
    (
        "NEW_NUMBER_CLAIM",
        "contextual",
        "supporting",
        r"\b(?:my new number|new phone number|changed my number|"
        r"lost my phone|new phone|new sim)\b",
        "Claims a new or changed phone number.",
    ),
    (
        "UNEXPECTED_CONTACT",
        "contextual",
        "weak",
        r"(?:\bis this [a-z][a-z .'-]{1,30}\?|\bwrong number\b|"
        r"\bsorry,? wrong number\b|\bfound your number\b|"
        r"\bdo i know you\b)",
        "Opens as an unexpected or wrong-number contact.",
    ),
    (
        "REPLY_OR_CALL_REQUEST",
        "operational",
        "supporting",
        rf"\b{CONTACT_VERBS}\b.{{0,30}}\b"
        rf"(?:me|us|this number|immediately|now|back)\b",
        "Requests direct contact or continuation.",
    ),
]


PROTECTIVE_RULES = [
    (
        "PROTECTIVE_DO_NOT_SHARE",
        rf"\b(?:do not|don't|never)\s+"
        rf"(?:share|send|give|provide)\b.{{0,45}}\b"
        rf"(?:{CODE_TERMS}|this code|the code|password|pin|cvv)\b"
        rf"|\b(?:{CODE_TERMS}|password|pin|cvv)\b.{{0,45}}\b"
        rf"(?:do not|don't|never)\s+(?:share|send|give|provide)\b",
        "Explicitly advises the recipient not to disclose a secret.",
    ),
    (
        "ANTI_SCAM_ADVICE",
        r"\b(?:ignore unknown sms|ignore suspicious messages?|report fraud|"
        r"beware of scams?|do not click suspicious links?|"
        r"never share your credentials?|we will never ask for your password|"
        r"we will never ask for your otp)\b",
        "Contains anti-fraud or protective guidance.",
    ),
]


URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>()]+")
SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rb.gy",
    "rebrand.ly",
    "shorturl.at",
}
BAIT_HOST_TERMS = {
    "secure",
    "verify",
    "verification",
    "login",
    "account",
    "update",
    "support",
    "wallet",
    "banking",
    "recover",
}


def _is_suspicious_url(raw: str) -> tuple[bool, str]:
    candidate = raw.rstrip(".,;:!?)]}")
    parsed = urlparse(
        candidate if "://" in candidate else f"https://{candidate}"
    )
    host = (parsed.hostname or "").lower()

    if not host:
        return True, "URL host could not be parsed reliably."

    if host in SHORTENERS or any(
        host.endswith("." + d) for d in SHORTENERS
    ):
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
        return True, (
            "Host contains multiple account/credential bait terms."
        )

    return False, ""


def detect_evidence(
    text: str,
) -> tuple[list[Evidence], list[Evidence]]:
    positive: list[Evidence] = []
    protective: list[Evidence] = []
    seen: set[tuple[str, int, int]] = set()

    request_ids = {
        "OTP_REQUEST",
        "CREDENTIAL_REQUEST",
        "FINANCIAL_INFO_REQUEST",
    }

    for evidence_id, category, strength, pattern, rationale in RULES:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            matched_lower = match.group(0).lower()

            # A household/network password is not an account credential.
            if (
                evidence_id == "CREDENTIAL_REQUEST"
                and re.search(
                    r"\b(?:wi[- ]?fi|wireless|network)\s+password\b",
                    matched_lower,
                    flags=re.IGNORECASE,
                )
            ):
                continue

            # "Do not share your OTP" is protective advice, not a request.
            if evidence_id in request_ids:
                prefix = text[
                    max(0, match.start() - 20):match.start()
                ]
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

            key = (
                evidence_id,
                match.start(),
                match.end(),
            )
            if key in seen:
                continue
            seen.add(key)

            positive.append(
                Evidence(
                    evidence_id,
                    category,
                    strength,
                    match.group(0),
                    match.start(),
                    match.end(),
                    rationale,
                )
            )

    for match in URL_RE.finditer(text):
        suspicious, rationale = _is_suspicious_url(
            match.group(0)
        )
        if suspicious:
            positive.append(
                Evidence(
                    "SUSPICIOUS_URL",
                    "operational",
                    "strong",
                    match.group(0),
                    match.start(),
                    match.end(),
                    rationale,
                )
            )

    for evidence_id, pattern, rationale in PROTECTIVE_RULES:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            protective.append(
                Evidence(
                    evidence_id,
                    "protective",
                    "protective",
                    match.group(0),
                    match.start(),
                    match.end(),
                    rationale,
                )
            )

    positive.sort(
        key=lambda item: (
            item.start,
            item.end,
            item.id,
        )
    )
    protective.sort(
        key=lambda item: (
            item.start,
            item.end,
            item.id,
        )
    )
    return positive, protective


