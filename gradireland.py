"""gradireland adapter.

gradireland's search page is client-rendered, but the XHR behind it is a plain
public JSON endpoint: no auth, no cookies, no custom headers. So this is a
direct POST rather than a scrape.

Two things the API does not do for us:
  - it returns roles outside Ireland, so regions are filtered here
  - it has no "posted in the last N hours" filter, so createdAt is filtered
    here instead. That is more precise than LinkedIn's fuzzy relative dates.
"""

import logging
from datetime import datetime, timedelta, timezone

import requests

log = logging.getLogger(__name__)

URL = "https://gradireland.com/ext/svc/inferno-search-service-1-0/search"
SITE = "gradireland"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://gradireland.com",
    "referer": "https://gradireland.com/search/jobs",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/151.0 Safari/537.36"
    ),
}

# Real region values from the API are "Ireland" or "County Dublin",
# "County Galway" and so on. "Europe" alone is not enough: the London
# internship in the sample carried ['England', 'Europe'].
IRISH_REGIONS = {"ireland", "republic of ireland", "all ireland"}

# Northern Ireland is UK jurisdiction, so a role there needs UK right to work
# rather than Irish. Off by default; flip if that changes.
INCLUDE_NORTHERN_IRELAND = False
NI_REGIONS = {"northern ireland", "belfast", "derry", "londonderry"}


def _payload(keyword, limit, offset=0):
    return {
        "fields": None,
        "keys": [keyword],
        "groupBy": None,
        # Excludes postings whose deadline has already passed.
        "conditionGroup": {
            "conjunction": "AND",
            "groups": [{
                "conjunction": "OR",
                "conditions": [{
                    "name": "application_deadline_date",
                    "value": ["0", "NOW"],
                    "operator": "NOT BETWEEN",
                }],
                "tags": ["facet:application_deadline_date"],
            }],
        },
        "facets": [],
        "sort": None,
        "conditions": [{"name": "type", "value": "opportunity", "operator": "="}],
        "limit": limit,
        "offset": offset,
        "includePromoted": False,
    }


def _in_ireland(doc):
    for raw in doc.get("regions") or []:
        region = str(raw).strip().lower()
        if region in NI_REGIONS:
            if INCLUDE_NORTHERN_IRELAND:
                return True
            continue
        # Counties come through as "County Dublin", "County Galway", ...
        if region in IRISH_REGIONS or region.startswith("county "):
            return True
    return False


def _recent(doc, cutoff):
    raw = doc.get("createdAt")
    if not raw:
        return True          # no timestamp: let dedupe decide instead
    try:
        created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return True
    return created >= cutoff


def _normalise(doc):
    """Map to the same shape every other source returns."""
    regions = doc.get("regions") or []
    return {
        "site": SITE,
        "id": str(doc.get("nid") or doc.get("uuid") or ""),
        "title": doc.get("title") or "",
        "company": doc.get("sourceOrganisationName") or "",
        "location": ", ".join(str(r) for r in regions) or "Ireland",
        "job_url": "https://gradireland.com" + (doc.get("path") or ""),
        "date_posted": (doc.get("createdAt") or "")[:10],
        "description": doc.get("body") or "",
    }


def _page(keyword, limit, offset, timeout):
    resp = requests.post(URL, headers=HEADERS,
                         json=_payload(keyword, limit, offset), timeout=timeout)
    resp.raise_for_status()
    return resp.json().get("search") or {}


def fetch(keywords, max_pages=10, page_size=60, timeout=30):
    """Return Irish jobs whose title matches any of `keywords`.

    gradireland is small (a few hundred live opportunities), and its search
    treats a multi-word key as a strict match, so "data engineer" returns
    almost nothing while "data" returns 130. Rather than fight that, this
    walks the whole live catalogue once and matches titles locally.

    There is no age filter: the API query already excludes postings whose
    application deadline has passed, and cross-run dedupe means anything
    already reported is never sent twice. Postings here sit open for months,
    so filtering on age would discard nearly everything.
    """
    needles = [k.lower() for k in keywords]
    out, seen, offset = [], set(), 0

    for _ in range(max_pages):
        search = _page("", page_size, offset, timeout)
        docs = search.get("documents") or []
        if not docs:
            break

        for doc in docs:
            if not _in_ireland(doc):
                continue
            title = (doc.get("title") or "").lower()
            if not any(n in title for n in needles):
                continue
            row = _normalise(doc)
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            out.append(row)

        offset += len(docs)
        if offset >= search.get("result_count", 0):
            break

    log.info("gradireland -> %d matching Irish roles from %d scanned",
             len(out), offset)
    return out
