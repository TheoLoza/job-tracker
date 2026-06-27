"""
config.py
---------
One place for all the settings the rest of the code reads.
Keeping this separate means the "what" (your values) lives here,
and the "how" (the logic) lives in the other files.
"""

import os
from dotenv import load_dotenv

# Reads the .env file in this folder and loads its KEY=VALUE pairs
# into environment variables that os.getenv() can see.
load_dotenv()

# ---- Notion ----
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ---- Gmail ----
# The OAuth client you downloaded from Google Cloud.
CLIENT_SECRET_FILE = "client_secret.json"
# Created automatically on first run; reused after that so you don't
# have to log in through the browser every time.
TOKEN_FILE = "token.json"

# Scope = what you're allowed to do.
# gmail.modify lets us READ messages AND add labels later (Phase 1+).
# If you want to be read-only for now, swap to: gmail.readonly
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


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
