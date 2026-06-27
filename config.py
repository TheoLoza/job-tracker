"""
config.py
---------
One place for all settings the rest of the code reads.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- Notion ----
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ---- Gmail ----
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
# gmail.modify = read messages AND add labels (we need both in Phase 1).
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# ---- Behaviour ----
# Gmail label stamped on emails we've handled, so they're never processed twice.
TRACKED_LABEL = "tracked"
# Only look at mail from the last N days (bounds work + speeds up each run).
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))
# DRY_RUN=true -> classify and print, but DON'T write to Notion or add labels.
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in ("1", "true", "yes", "on")


def check():
    """Fail loudly and early if a secret is missing, with a clear reason."""
    missing = []
    if not NOTION_TOKEN:
        missing.append("NOTION_TOKEN")
    if not NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")
    if missing:
        raise SystemExit(
            f"Missing {', '.join(missing)} — did you copy .env.example to .env "
            f"and fill it in?"
        )
    if not os.path.exists(CLIENT_SECRET_FILE):
        raise SystemExit(
            f"Can't find {CLIENT_SECRET_FILE} — drop the JSON you downloaded "
            f"from Google Cloud into this folder."
        )
