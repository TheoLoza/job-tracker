"""
notion_writer.py
----------------
Talk to Notion via raw REST: create rows, find an existing application, and
update a row's status. We use `requests` (not an SDK) so the API is visible.

Property shapes (the KEYS must match your DB column names EXACTLY):
  title     -> {"title":     [{"text": {"content": "..."}}]}
  rich_text -> {"rich_text": [{"text": {"content": "..."}}]}
  select    -> {"select": {"name": "Applied"}}
  date      -> {"date": {"start": "2026-06-27"}}
  url       -> {"url": "https://..."}
"""

import datetime
import requests

import config

BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {config.NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _check(resp):
    if resp.status_code != 200:
        # Surface Notion's actual complaint. Classic ones:
        #   "Could not find database" -> integration not connected / wrong id
        #   property errors           -> a column name below doesn't match your DB
        raise RuntimeError(f"Notion API error {resp.status_code}: {resp.text}")
    return resp.json()


def create_row(company, role, status, date_applied=None, notes="", email_link=None):
    """Create one row and return its Notion URL."""
    today = datetime.date.today().isoformat()
    props = {
        "Company": {"title": [{"text": {"content": company or "Unknown"}}]},
        "Role": {"rich_text": [{"text": {"content": role or ""}}]},
        "Status": {"select": {"name": status}},
        "Date Applied": {"date": {"start": date_applied or today}},
        "Last Update": {"date": {"start": today}},
        "Notes": {"rich_text": [{"text": {"content": notes or ""}}]},
    }
    if email_link:
        props["Email Link"] = {"url": email_link}
    payload = {"parent": {"database_id": config.NOTION_DATABASE_ID}, "properties": props}
    return _check(requests.post(f"{BASE}/pages", headers=HEADERS, json=payload)).get("url")


def find_open_application(company):
    """
    Return the page id of an existing 'Applied' row whose Company contains the
    given name (Notion's `contains` is case-insensitive), or None.

    NOTE: this is the fuzzy-matching part. In Phase 1 we match on company name
    only, which can miss when the rejection email names the company differently
    than the application email did. Phase 3 will make matching smarter.
    """
    if not company:
        return None
    payload = {
        "filter": {
            "and": [
                {"property": "Company", "title": {"contains": company}},
                {"property": "Status", "select": {"equals": "Applied"}},
            ]
        },
        "page_size": 1,
    }
    data = _check(
        requests.post(
            f"{BASE}/databases/{config.NOTION_DATABASE_ID}/query",
            headers=HEADERS, json=payload,
        )
    )
    results = data.get("results", [])
    return results[0]["id"] if results else None


def update_status(page_id, status):
    """Flip an existing row's Status and bump Last Update to today."""
    payload = {
        "properties": {
            "Status": {"select": {"name": status}},
            "Last Update": {"date": {"start": datetime.date.today().isoformat()}},
        }
    }
    return _check(requests.patch(f"{BASE}/pages/{page_id}", headers=HEADERS, json=payload)).get("url")
