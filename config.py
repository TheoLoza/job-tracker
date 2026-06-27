"""
config.py
---------
One place for all settings the rest of the code reads.
Everything here is free — no paid APIs.
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
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# ---- Behaviour ----
TRACKED_LABEL = "tracked"
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))
# DRY_RUN=true -> classify and print, but DON'T write to Notion or add labels.
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() in ("1", "true", "yes", "on")


def check():
    """Fail loudly and early if a required secret is missing."""
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
