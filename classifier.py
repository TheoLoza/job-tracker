"""
classifier.py
-------------
Rules-based email classifier for Phase 1. No AI yet — just sender domains and
keyword matching. Returns: {"status", "company", "role"}.

status is one of: "Applied", "Rejected", "Ignore".

This is deliberately simple and transparent. Phase 2 will hand the ambiguous
cases to an LLM and do much better company/role extraction.
"""

import re

# Mail from these applicant-tracking-system / careers senders is very likely
# job-related, which raises our confidence that it's worth classifying.
ATS_DOMAINS = (
    "greenhouse.io", "greenhouse-mail.io", "lever.co", "hire.lever.co",
    "ashbyhq.com", "myworkday.com", "myworkdayjobs.com", "icims.com",
    "smartrecruiters.com", "taleo.net", "successfactors.com", "jobvite.com",
    "workable.com", "breezy.hr", "bamboohr.com", "rippling.com",
)

# Checked FIRST — rejections are often phrased politely and also contain
# "thank you for applying" type language, so rejection signals win ties.
REJECTION_PHRASES = (
    "unfortunately", "we regret", "regret to inform", "not moving forward",
    "will not be moving forward", "won't be moving forward", "not be moving forward",
    "decided not to", "move forward with other", "other candidates",
    "not be proceeding", "no longer under consideration", "not selected",
    "were not selected", "position has been filled", "pursue other",
    "wish you the best", "wish you success", "not a match at this time",
    "decided to proceed with other",
)

# Confirmation-of-application signals.
APPLIED_PHRASES = (
    "application received", "we received your application", "received your application",
    "thank you for applying", "thanks for applying", "application has been received",
    "successfully submitted", "successfully applied", "your application to",
    "we have received your application", "application was sent", "application is in",
)


def _domain(from_header):
    m = re.search(r"@([\w.-]+)", from_header or "")
    return m.group(1).lower() if m else ""


def _blob(email):
    return f"{email['subject']} {email['snippet']} {email['body']}".lower()


def _looks_job_related(email, domain):
    if any(domain.endswith(d) for d in ATS_DOMAINS):
        return True
    text = _blob(email)
    return any(p in text for p in APPLIED_PHRASES + REJECTION_PHRASES)


def _guess_company(email, domain):
    """Best-effort company name from subject patterns or the sender name."""
    subject = email["subject"] or ""
    for pat in (
        r"application to ([A-Z][\w&.\- ]+)",
        r"applying to ([A-Z][\w&.\- ]+)",
        r"interest in ([A-Z][\w&.\- ]+)",
        r"\bat ([A-Z][\w&.\- ]+)",
    ):
        m = re.search(pat, subject)
        if m:
            return m.group(1).strip(" .!-")
    # Fall back to the From display name, e.g. "Acme Careers <no-reply@...>".
    m = re.match(r'\s*"?([^"<]+?)"?\s*<', email["from"] or "")
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
    subject = email["subject"] or ""
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
    domain = _domain(email["from"])

    if not _looks_job_related(email, domain):
        return {"status": "Ignore", "company": "", "role": ""}

    text = _blob(email)
    if any(p in text for p in REJECTION_PHRASES):
        status = "Rejected"
    elif any(p in text for p in APPLIED_PHRASES):
        status = "Applied"
    else:
        # Job-related sender but no clear signal — leave for Phase 2's LLM.
        return {"status": "Ignore", "company": "", "role": ""}

    return {
        "status": status,
        "company": _guess_company(email, domain),
        "role": _guess_role(email),
    }
