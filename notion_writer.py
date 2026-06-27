"""
notion_writer.py
----------------
Writes a single row (a "page") into your Notion database using the raw REST
API via `requests`. We do this by hand (instead of a Notion SDK) so you can
see exactly what the API expects — this is the part worth understanding.

Key idea: every Notion property type has its OWN shape in the JSON.
  - title     -> {"title":     [{"text": {"content": "..."}}]}
  - rich_text -> {"rich_text": [{"text": {"content": "..."}}]}
  - select    -> {"select": {"name": "Applied"}}
  - date      -> {"date": {"start": "2026-06-27"}}
  - url       -> {"url": "https://..."}
The KEYS ("Company", "Status", ...) must match your DB column names EXACTLY.
"""

import requests

import config

NOTION_API = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {config.NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",   # pin a version so the API shape is stable
    "Content-Type": "application/json",
}


def create_row(company, role, status, date_applied, notes="", email_link=None):
    """
    Create one row in the database. Returns the new page's URL on success.
    Raises with Notion's error message if something's off (e.g. a column name
    typo, or the integration not being connected to the DB).
    """
    properties = {
        "Company": {"title": [{"text": {"content": company}}]},
        "Role": {"rich_text": [{"text": {"content": role}}]},
        "Status": {"select": {"name": status}},
        "Date Applied": {"date": {"start": date_applied}},
        "Notes": {"rich_text": [{"text": {"content": notes}}]},
    }
    # URL property only accepts a real URL or null — skip it if we don't have one.
    if email_link:
        properties["Email Link"] = {"url": email_link}

    payload = {
        "parent": {"database_id": config.NOTION_DATABASE_ID},
        "properties": properties,
    }

    resp = requests.post(NOTION_API, headers=HEADERS, json=payload)

    if resp.status_code != 200:
        # Surface Notion's actual complaint instead of a generic error.
        # The classic one here is "Could not find database" = integration
        # isn't connected to the DB, or the id is wrong.
        raise RuntimeError(f"Notion API error {resp.status_code}: {resp.text}")

    return resp.json().get("url")
