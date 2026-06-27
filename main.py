"""
main.py — PHASE 1
-----------------
Reads untracked inbox mail, classifies each email with simple rules, and
records it in Notion:
  - Applied  -> create a new row
  - Rejected -> update the matching 'Applied' row (or create one if none found)
  - Ignore   -> skip, leave unlabeled so smarter logic later can re-check it

Emails we act on get the `tracked` Gmail label, so they're never handled twice.

TIP: set DRY_RUN=true in your .env to classify and print WITHOUT writing to
Notion or labeling — great for sanity-checking the rules against real mail.
"""

import config
import gmail_client
import notion_writer
from classifier import classify


def handle(email, result):
    """Act on one classified email. Returns a log string, or None if ignored."""
    status, company, role = result["status"], result["company"], result["role"]

    if status == "Applied":
        notion_writer.create_row(company, role, "Applied", notes=email["subject"])
        return f"Applied   {company} ({role or 'role?'})"

    if status == "Rejected":
        page_id = notion_writer.find_open_application(company)
        if page_id:
            notion_writer.update_status(page_id, "Rejected")
            return f"Rejected  {company} (updated existing row)"
        notion_writer.create_row(company, role, "Rejected", notes=email["subject"])
        return f"Rejected  {company} (no match found, created row)"

    return None  # Ignore


def main():
    config.check()
    service = gmail_client.authenticate()

    print("Fetching untracked inbox mail...")
    emails = gmail_client.get_untracked_messages(service)
    if not emails:
        print("Nothing new to process.")
        return
    print(f"Found {len(emails)} email(s) to look at.\n")

    label_id = None if config.DRY_RUN else gmail_client.ensure_label(service)
    counts = {"Applied": 0, "Rejected": 0, "Ignore": 0}

    for email in emails:
        result = classify(email)
        counts[result["status"]] = counts.get(result["status"], 0) + 1

        if config.DRY_RUN:
            print(f"[dry-run] {result['status']:8} | {email['subject'][:65]}")
            continue

        msg = handle(email, result)
        if msg:
            print("  " + msg)
            # Only label emails we acted on; ignored mail stays unlabeled so a
            # future (smarter) run can reconsider it.
            gmail_client.mark_tracked(service, email["id"], label_id)

    print(
        f"\nDone. Applied: {counts['Applied']}  "
        f"Rejected: {counts['Rejected']}  Ignored: {counts['Ignore']}"
    )
    if config.DRY_RUN:
        print("(DRY_RUN was on — nothing was written to Notion or labeled.)")


if __name__ == "__main__":
    main()
