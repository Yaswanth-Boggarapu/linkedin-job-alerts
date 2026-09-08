"""Read the Notion applications tracker so already-actioned roles stay out.

The tracker is the system of record for what has been applied to. Without
this the pipeline happily re-surfaces a job that was applied to last week,
because dedupe only knows what it has *reported*, not what was *done*.

Disabled unless NOTION_TOKEN and NOTION_DB are set; a failure here never
blocks a run.
"""

import logging
import os
import re

import requests

log = logging.getLogger(__name__)

TOKEN = os.environ.get("NOTION_TOKEN", "")
DB = os.environ.get("NOTION_DB", "")
API = "https://api.notion.com/v1"
VERSION = "2022-06-28"

_ID = re.compile(r"(\d{6,})")


def enabled():
    return bool(TOKEN and DB)


def _rows(timeout):
    """Every page in the tracker database, following pagination."""
    out, cursor = [], None
    headers = {"Authorization": f"Bearer {TOKEN}",
               "Notion-Version": VERSION,
               "Content-Type": "application/json"}
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = requests.post(f"{API}/databases/{DB}/query",
                             headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        out.extend(data.get("results", []))
        if not data.get("has_more"):
            return out
        cursor = data.get("next_cursor")


def _values(page):
    """Any URL or plain-text value on a page, flattened."""
    found = []
    for prop in (page.get("properties") or {}).values():
        kind = prop.get("type")
        if kind == "url" and prop.get("url"):
            found.append(prop["url"])
        elif kind in ("title", "rich_text"):
            for chunk in prop.get(kind) or []:
                text = (chunk.get("plain_text") or "").strip()
                if text:
                    found.append(text)
    return found


def applied_keys(timeout=30):
    """Return a set of identifiers for roles already in the tracker.

    Matches on both the job URL and any long numeric id inside it, since the
    URL stored by hand rarely matches the scraped one character for character.
    """
    if not enabled():
        return set()

    keys = set()
    try:
        for page in _rows(timeout):
            for value in _values(page):
                low = value.lower().strip().rstrip("/")
                if low.startswith("http"):
                    keys.add(low.split("?")[0])
                    m = _ID.search(low)
                    if m:
                        keys.add(m.group(1))
    except Exception as exc:
        log.warning("notion lookup failed, not filtering: %s", exc)
        return set()

    log.info("notion tracker: %d identifiers", len(keys))
    return keys


def already_applied(job, keys):
    if not keys:
        return False
    url = (job.get("job_url") or "").lower().rstrip("/").split("?")[0]
    if url and url in keys:
        return True
    jid = str(job.get("id") or "")
    return bool(jid) and len(jid) >= 6 and jid in keys
