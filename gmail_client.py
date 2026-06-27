"""
gmail_client.py
---------------
Two jobs:
  1. authenticate()      -> logs into Gmail (once via browser, then cached)
  2. get_latest_message  -> pulls the most recent inbox email as a tidy dict

You generally won't need to touch the auth dance — it's standard Google
boilerplate. The interesting part for later phases is how we read and parse
messages.
"""

import os
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def authenticate():
    """
    Returns an authorized Gmail 'service' object you can make API calls on.

    Flow:
      - If token.json exists and is valid -> use it (no browser).
      - If it's expired but refreshable     -> refresh silently.
      - Otherwise                           -> open a browser to log in,
                                               then SAVE token.json for next time.
    """
    creds = None

    # token.json stores your access + refresh tokens from a previous run.
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)

    # No (valid) credentials available -> get some.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # silent refresh, no browser
        else:
            # First-ever run: this pops open a browser window asking you to
            # pick your job-hunt Gmail account and approve access.
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CLIENT_SECRET_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save so the next run skips the browser entirely.
        # (This token.json is what GitHub Actions will use later to run unattended.)
        with open(config.TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _header(headers, name):
    """Pull a single header value (e.g. 'Subject') out of Gmail's header list."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def get_latest_message(service):
    """
    Grab the single most recent message from the inbox and return a small,
    friendly dict. Returns None if the inbox is empty.
    """
    # Step 1: list message IDs (this does NOT include the content yet).
    resp = (
        service.users()
        .messages()
        .list(userId="me", maxResults=1, labelIds=["INBOX"])
        .execute()
    )
    messages = resp.get("messages", [])
    if not messages:
        return None

    # Step 2: fetch the full message by id.
    msg_id = messages[0]["id"]
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

    headers = msg["payload"].get("headers", [])
    return {
        "id": msg_id,
        "from": _header(headers, "From"),
        "subject": _header(headers, "Subject"),
        "snippet": msg.get("snippet", ""),  # Gmail's short preview text
    }
