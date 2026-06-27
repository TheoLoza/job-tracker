"""
gmail_client.py
---------------
Gmail auth, reading untracked mail, and labeling.
"""

import os
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def authenticate():
    """Return an authorized Gmail service (browser login once, then cached)."""
    creds = None
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # silent refresh, no browser
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CLIENT_SECRET_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode(data):
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")


def _extract_body(payload):
    """Walk the MIME tree and return plain-text body (best effort)."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    text = ""
    for part in payload.get("parts", []) or []:
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            text += _decode(part["body"]["data"])
        elif mime.startswith("multipart/"):
            text += _extract_body(part)  # nested parts
    return text


def _parse(msg):
    headers = msg["payload"].get("headers", [])
    return {
        "id": msg["id"],
        "from": _header(headers, "From"),
        "subject": _header(headers, "Subject"),
        "snippet": msg.get("snippet", ""),
        "body": _extract_body(msg["payload"])[:5000],  # cap; only used for keywords
    }


def get_untracked_messages(service, max_results=25):
    """
    Parsed inbox emails we haven't tagged yet. The Gmail query excludes the
    `tracked` label, so each email is handled exactly once across runs.
    """
    query = f"in:inbox -label:{config.TRACKED_LABEL} newer_than:{config.LOOKBACK_DAYS}d"
    resp = (
        service.users().messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    out = []
    for m in resp.get("messages", []):
        full = service.users().messages().get(userId="me", id=m["id"], format="full").execute()
        out.append(_parse(full))
    return out


def ensure_label(service):
    """Return the id of the `tracked` label, creating it if it doesn't exist."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for lbl in labels:
        if lbl["name"].lower() == config.TRACKED_LABEL.lower():
            return lbl["id"]
    created = (
        service.users().labels()
        .create(userId="me", body={"name": config.TRACKED_LABEL})
        .execute()
    )
    return created["id"]


def mark_tracked(service, msg_id, label_id):
    """Stamp the `tracked` label so future runs skip this message."""
    service.users().messages().modify(
        userId="me", id=msg_id, body={"addLabelIds": [label_id]}
    ).execute()
