"""
classifier.py
-------------
Rules-based email classifier. Free, transparent, no AI. Returns:
  {"status", "company", "role"}  where status is "Applied" / "Rejected" / "Ignore".

When an email is a FORWARD, we classify using the ORIGINAL sender/subject
(parsed out of the body by gmail_client) instead of the outer header — so the
company comes out right even though you forwarded the mail to yourself.
"""

import re

ATS_DOMAINS = (
    "greenhouse.io", "greenhouse-mail.io", "lever.co", "hire.lever.co",
    "ashbyhq.com", "myworkday.com", "myworkdayjobs.com", "icims.com",
    "smartrecruiters.com", "taleo.net", "successfactors.com", "jobvite.com",
    "workable.com", "breezy.hr", "bamboohr.com", "rippling.com",
)

# Checked FIRST — rejections are often polite and also say "thanks for applying".
REJECTION_PHRASES = (
    "unfortunately", "we regret", "regret to inform", "not moving forward",
    "will not be moving forward", "won't be moving forward", "not be moving forward",
    "decided not to", "move forward with other", "other candidates",
    "not be proceeding", "no longer under consideration", "not selected",
    "were not selected", "position has been filled", "pursue other",
    "wish you the best", "wish you success", "not a match at this time",
    "decided to proceed with other",
)

APPLIED_PHRASES = (
    "application received", "we received your application", "received your application",
    "thank you for applying", "thanks for applying", "application has been received",
    "successfully submitted", "successfully applied", "your application to",
    "we have received your application", "application was sent", "application is in",
)


# ---- forward-aware accessors: prefer the ORIGINAL sender/subject if present ----
def _eff_from(email):
    return email.get("original_from") or email.get("from", "")


def _eff_subject(email):
    return email.get("original_subject") or email.get("subject", "")


def _domain(email):
    m = re.search(r"@([\w.-]+)", _eff_from(email) or "")
    return m.group(1).lower() if m else ""


def _blob(email):
    # Body always included so keyword checks work even on odd subjects.
    return f"{_eff_subject(email)} {email.get('snippet','')} {email.get('body','')}".lower()


def _looks_job_related(email, domain):
    if any(domain.endswith(d) for d in ATS_DOMAINS):
        return True
    text = _blob(email)
    return any(p in text for p in APPLIED_PHRASES + REJECTION_PHRASES)


def _guess_company(email, domain):
    """Best-effort company name from subject patterns or the sender name."""
    subject = _eff_subject(email) or ""
    for pat in (
        r"application to ([A-Z][\w&.\- ]+)",
        r"applying to ([A-Z][\w&.\- ]+)",
        r"interest in ([A-Z][\w&.\- ]+)",
        r"\bat ([A-Z][\w&.\- ]+)",
    ):
        m = re.search(pat, subject)
        if m:
            return m.group(1).strip(" .!-")
    # Fall back to the (original) From display name, e.g. "Acme Careers <...>".
    m = re.match(r'\s*"?([^"<]+?)"?\s*<', _eff_from(email) or "")
    if m:
        name = m.group(1).strip()
        for junk in ("careers", "recruiting", "talent", "no-?reply", "hr", "team", "jobs"):
            name = re.sub(junk, "", name, flags=re.I)
        name = name.strip(" -|·,")
        if name:
            return name
    parts = domain.split(".")
    return parts[-2].capitalize() if len(parts) >= 2 else (domain or "Unknown")


def _guess_role(email):
    subject = _eff_subject(email) or ""
    for pat in (
        r"application (?:received|for)[:\-]?\s*(.+)",
        r"your application for[:\-]?\s*(.+)",
        r"applying for[:\-]?\s*(.+)",
        r"the (.+?) (?:role|position)",
    ):
        m = re.search(pat, subject, flags=re.I)
        if m:
            role = re.split(r"\s+at\s+", m.group(1).strip(" .!-"))[0].strip()
            if role:
                return role
    return ""


def classify(email):
    domain = _domain(email)

    if not _looks_job_related(email, domain):
        return {"status": "Ignore", "company": "", "role": ""}

    text = _blob(email)
    if any(p in text for p in REJECTION_PHRASES):
        status = "Rejected"
    elif any(p in text for p in APPLIED_PHRASES):
        status = "Applied"
    else:
        return {"status": "Ignore", "company": "", "role": ""}

    return {
        "status": status,
        "company": _guess_company(email, domain),
        "role": _guess_role(email),
    }
