
"""analyzer.py — Header parsing, DNS checks, scoring.

This file contains the core analysis functions used by the Flask app.

High-level structure (for beginners):
- Parsing helpers: extract emails, domains, display names, sending IPs
- DNS checks: SPF, DKIM, DMARC lookups using dnspython
- Heuristics: reply-to, display-name impersonation, sending IP checks
- Scoring: convert check results into a numeric risk score + verdict

Related files in this project:
- app.py         — Flask routes that call `analyse()` and render templates
- templates/     — UI templates that display results (index.html, results.html)
- static/        — CSS and frontend assets

Tips for reading the code:
- Start at `analyse(raw_header)` — this is the main entry point.
- Follow `parse_headers()` to see what fields are extracted from the raw header.
- Each `check_*` function returns a small dict: {"status": ..., "detail": ...}.

"""

import re
import ipaddress
from email import message_from_string
import dns.resolver
import dns.exception

# Known brands we check for in display names (simple keyword list)
KNOWN_BRANDS = [
    "paypal", "apple", "microsoft", "amazon", "google", "netflix",
    "facebook", "instagram", "twitter", "linkedin", "dropbox",
    "chase", "bank of america", "wells fargo", "hsbc", "barclays",
    "hmrc", "irs", "dhl", "fedex", "ups", "royal mail",
]

# Some TLDs that are often used for malicious purposes — used as heuristic
SUSPICIOUS_TLDS = [".xyz", ".top", ".click", ".loan", ".work", ".gq", ".cf", ".tk", ".ml", ".ga"]


def parse_headers(raw_header: str) -> dict:
    """Parse a raw RFC-822 header string into useful fields.

    Returns a dict with extracted values the rest of the analyzer uses.
    This isolates parsing details from the checks and scoring logic.
    """
    msg = message_from_string(raw_header)

    # Raw header fields we care about — use empty string when missing
    from_field = msg.get("From", "")
    reply_to_field = msg.get("Reply-To", "")
    subject = msg.get("Subject", "")
    date = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    # Normalised extracted values for easier checks later
    from_email = _extract_email(from_field)
    from_domain = _extract_domain(from_email)
    display_name = _extract_display_name(from_field)

    reply_to_email = _extract_email(reply_to_field)
    reply_to_domain = _extract_domain(reply_to_email)

    # Sending IP is extracted from Received headers (best-effort)
    sending_ip = _extract_sending_ip(raw_header)

    return {
        "from_field": from_field,
        "from_email": from_email,
        "from_domain": from_domain,
        "display_name": display_name,
        "reply_to_field": reply_to_field,
        "reply_to_email": reply_to_email,
        "reply_to_domain": reply_to_domain,
        "sending_ip": sending_ip,
        "subject": subject,
        "date": date,
        "message_id": message_id,
    }


def _extract_email(field: str) -> str:
    """Return the email address from a header field.

    Examples:
    - 'Alice Example <alice@example.com>' -> 'alice@example.com'
    - 'bob@example.com' -> 'bob@example.com'
    """
    match = re.search(r"<([^>]+)>", field)
    if match:
        return match.group(1).strip().lower()
    field = field.strip().lower()
    if "@" in field:
        return field
    return ""


def _extract_domain(email: str) -> str:
    """Return the domain portion of an email address, or empty string.

    e.g. 'alice@example.com' -> 'example.com'
    """
    if "@" in email:
        return email.split("@")[1].strip()
    return ""


def _extract_display_name(from_field: str) -> str:
    """Try to extract the human-readable display name from the From header.

    e.g. '"PayPal" <notify@paypal.com>' -> 'PayPal'
    """
    match = re.match(r'^"?([^"<]+)"?\s*<', from_field)
    if match:
        return match.group(1).strip()
    return ""


def _extract_sending_ip(raw_header: str) -> str:
    """Best-effort: find the first public IPv4 address from Received headers.

    - Scans 'Received:' headers for bracketed IPs (common format).
    - Skips private and loopback addresses.
    - Falls back to any public-looking IP in the whole header.
    """
    # Walk Received headers top-to-bottom; return first public IP found
    received_headers = re.findall(r"Received:.*?(?=\nReceived:|\nFrom:|\nTo:|\Z)", raw_header, re.DOTALL | re.IGNORECASE)
    for header in received_headers:
        ips = re.findall(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]", header)
        for ip in ips:
            try:
                obj = ipaddress.ip_address(ip)
                if not obj.is_private and not obj.is_loopback:
                    return ip
            except ValueError:
                continue
    # Fallback: any IP in headers
    all_ips = re.findall(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", raw_header)
    for ip in all_ips:
        try:
            obj = ipaddress.ip_address(ip)
            if not obj.is_private and not obj.is_loopback:
                return ip
        except ValueError:
            continue
    return ""


# ---------------------------------------------------------------------------
# DNS checks
# ---------------------------------------------------------------------------

def check_spf(domain: str) -> dict:
    """Look up TXT records for SPF and return a simple status dict.

    Note: This is a heuristic — full SPF evaluation requires checking the
    sending IP against each mechanism. Here we only detect presence and
    obviously permissive/strict qualifiers for a quick portfolio demo.
    """
    if not domain:
        return {"status": "not_found", "detail": "No domain found"}
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            txt = "".join(s.decode() if isinstance(s, bytes) else s for s in rdata.strings)
            if txt.startswith("v=spf1"):
                if "~all" in txt or "-all" in txt:
                    return {"status": "pass", "detail": txt}
                elif "?all" in txt or "+all" in txt:
                    return {"status": "fail", "detail": txt}
                return {"status": "pass", "detail": txt}
        return {"status": "not_found", "detail": "No SPF record found"}
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {"status": "not_found", "detail": "No SPF record found"}
    except dns.exception.DNSException as e:
        return {"status": "error", "detail": str(e)}


def check_dmarc(domain: str) -> dict:
    """Fetch the DMARC TXT record for the domain and return status.

    We look for 'v=DMARC1' and the 'p=' policy to give a quick pass/fail.
    """
    if not domain:
        return {"status": "not_found", "detail": "No domain found"}
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in answers:
            txt = "".join(s.decode() if isinstance(s, bytes) else s for s in rdata.strings)
            if "v=DMARC1" in txt:
                if "p=reject" in txt or "p=quarantine" in txt:
                    return {"status": "pass", "detail": txt}
                elif "p=none" in txt:
                    return {"status": "fail", "detail": txt}
                return {"status": "pass", "detail": txt}
        return {"status": "not_found", "detail": "No DMARC record found"}
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {"status": "not_found", "detail": "No DMARC record found"}
    except dns.exception.DNSException as e:
        return {"status": "error", "detail": str(e)}


def check_dkim(domain: str, raw_header: str) -> dict:
    """Detect DKIM selector in the header and check DNS for the public key.

    This function does not verify the signature cryptographically — it only
    checks whether a public key record exists for the selector/domain.
    """
    # Extract DKIM-Signature selector
    match = re.search(r"DKIM-Signature:.*?s=([a-zA-Z0-9_.-]+)", raw_header, re.DOTALL | re.IGNORECASE)
    if not match:
        return {"status": "not_found", "detail": "No DKIM-Signature header present"}
    selector = match.group(1).strip()
    lookup = f"{selector}._domainkey.{domain}"
    try:
        answers = dns.resolver.resolve(lookup, "TXT")
        for rdata in answers:
            txt = "".join(s.decode() if isinstance(s, bytes) else s for s in rdata.strings)
            if "p=" in txt:
                return {"status": "pass", "detail": f"Key found at {lookup}"}
        return {"status": "not_found", "detail": f"No DKIM key at {lookup}"}
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return {"status": "not_found", "detail": f"No DKIM key at {lookup}"}
    except dns.exception.DNSException as e:
        return {"status": "error", "detail": str(e)}


def check_reply_to(from_domain: str, reply_to_domain: str) -> dict:
    """Simple check: is the Reply-To domain different from the From domain?

    A differing Reply-To is a common phishing indicator (but not definitive).
    """
    if not reply_to_domain:
        return {"status": "pass", "detail": "No Reply-To header"}
    if from_domain and reply_to_domain and from_domain != reply_to_domain:
        return {"status": "fail", "detail": f"Reply-To domain ({reply_to_domain}) differs from From domain ({from_domain})"}
    return {"status": "pass", "detail": "Reply-To matches From domain"}


def check_display_name(display_name: str, from_email: str) -> dict:
    """Heuristic: if display name includes a known brand but the sending
    email is not from that brand, mark as suspicious.
    """
    if not display_name:
        return {"status": "pass", "detail": "No display name"}
    name_lower = display_name.lower()
    for brand in KNOWN_BRANDS:
        if brand in name_lower:
            # Check if the sending domain is actually that brand
            if brand not in from_email.lower():
                return {"status": "fail", "detail": f"Display name contains '{brand}' but sending domain is '{from_email}'"}
    return {"status": "pass", "detail": "No brand impersonation detected"}


def check_sending_ip(ip: str) -> dict:
    """Check the sending IP for obvious problems and weak heuristics.

    - Flags private/loopback addresses (unlikely for real external mail).
    - Attempts a PTR lookup and flags suspicious reverse-DNS TLDs.
    """
    if not ip:
        return {"status": "pass", "detail": "No sending IP extracted"}
    try:
        obj = ipaddress.ip_address(ip)
        if obj.is_private:
            return {"status": "fail", "detail": f"{ip} is a private/internal address"}
        if obj.is_loopback:
            return {"status": "fail", "detail": f"{ip} is a loopback address"}
    except ValueError:
        return {"status": "fail", "detail": f"Invalid IP: {ip}"}

    # Reverse DNS check for suspicious TLDs
    try:
        import dns.reversename

        rev = dns.resolver.resolve(dns.reversename.from_address(ip), "PTR")
        rdns = str(rev[0]).lower()
        for tld in SUSPICIOUS_TLDS:
            if rdns.endswith(tld.lstrip(".")):
                return {"status": "fail", "detail": f"Reverse DNS ({rdns}) has suspicious TLD"}
        return {"status": "pass", "detail": f"Reverse DNS: {rdns}"}
    except Exception:
        return {"status": "pass", "detail": f"No reverse DNS for {ip}"}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

SCORE_MAP = {
    "spf":          {"fail": 25, "not_found": 10, "error": 5},
    "dkim":         {"fail": 20, "not_found": 8,  "error": 4},
    "dmarc":        {"fail": 25, "not_found": 8,  "error": 4},
    "reply_to":     {"fail": 15},
    "display_name": {"fail": 10},
    "sending_ip":   {"fail": 10},
}

VERDICT_THRESHOLDS = [
    (0,  24,  "LIKELY LEGITIMATE", "green"),
    (25, 54,  "SUSPICIOUS",        "amber"),
    (55, 100, "LIKELY PHISHING",   "red"),
]


def calculate_score(checks: dict) -> tuple[int, str, str]:
    """Convert individual check statuses into a numeric risk score.

    - `checks` is a mapping of check name -> {"status":..., "detail":...}
    - Uses `SCORE_MAP` to add points for failed/missing checks.
    - Returns: (score, verdict_text, colour)
    """
    score = 0
    for key, result in checks.items():
        status = result.get("status", "pass")
        if status in SCORE_MAP.get(key, {}):
            score += SCORE_MAP[key][status]
    score = min(score, 100)

    for low, high, verdict, colour in VERDICT_THRESHOLDS:
        if low <= score <= high:
            return score, verdict, colour

    return score, "SUSPICIOUS", "amber"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyse(raw_header: str) -> dict:
    """Main entry point: run all parsing, checks and scoring on a header.

    Returns a dictionary containing parsed fields, detailed checks,
    a numeric score and a human verdict + colour for simple UI mapping.
    """
    parsed = parse_headers(raw_header)
    domain = parsed["from_domain"]

    # Run each check and collect structured results
    checks = {
        "spf":          check_spf(domain),
        "dkim":         check_dkim(domain, raw_header),
        "dmarc":        check_dmarc(domain),
        "reply_to":     check_reply_to(parsed["from_domain"], parsed["reply_to_domain"]),
        "display_name": check_display_name(parsed["display_name"], parsed["from_email"]),
        "sending_ip":   check_sending_ip(parsed["sending_ip"]),
    }

    score, verdict, colour = calculate_score(checks)

    return {
        "parsed": parsed,
        "checks": checks,
        "score": score,
        "verdict": verdict,
        "colour": colour,
    }
