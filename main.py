"""
main.py  —  PHASE 0
-------------------
Goal: prove the two pipes connect. No classification, no logic yet.

What it does:
  1. Authenticates to Gmail.
  2. Reads the most recent email in the inbox.
  3. Writes ONE test row to your Notion database, stuffing that email's
     subject + snippet into the Notes field.

If a new row shows up in Notion containing text from a real email in your
inbox, BOTH halves of the system work and you're ready for Phase 1.
"""

import datetime

import config
import gmail_client
import notion_writer


def main():
    # Bail early with a clear message if a secret/file is missing.
    config.check()

    print("Authenticating to Gmail...")
    service = gmail_client.authenticate()

    print("Reading your latest inbox message...")
    email = gmail_client.get_latest_message(service)

    if email is None:
        print("Inbox is empty — send yourself a test email and rerun.")
        return

    print(f"  From:    {email['from']}")
    print(f"  Subject: {email['subject']}")

    print("Writing a test row to Notion...")
    today = datetime.date.today().isoformat()  # e.g. "2026-06-27"
    url = notion_writer.create_row(
        company="TEST ROW — delete me",
        role="(phase 0 connectivity check)",
        status="Applied",
        date_applied=today,
        notes=f"Latest email was: {email['subject']} — {email['snippet']}",
    )

    print(f"\n Done. Row created: {url}")
    print("Open your Notion DB — if you see that row, Phase 0 passed.")


if __name__ == "__main__":
    main()
