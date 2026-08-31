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


def fetch(keyword, hours_old=720, limit=60, timeout=30):
    """Return a list of job dicts for one keyword.

    The default window is deliberately wide (30 days). gradireland postings sit
    open for months: of 209 sampled, none were under a day old and only four
    were under a week. Dedupe means each job is still only reported once, so a
    wide window just means "anything not seen before".
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_old)

    resp = requests.post(URL, headers=HEADERS,
                         json=_payload(keyword, limit), timeout=timeout)
    resp.raise_for_status()
    search = resp.json().get("search") or {}
    docs = search.get("documents") or []

    out, dropped_region, dropped_age = [], 0, 0
    for doc in docs:
        if not _in_ireland(doc):
            dropped_region += 1
            continue
        if not _recent(doc, cutoff):
            dropped_age += 1
            continue
        out.append(_normalise(doc))

    log.info("gradireland/%s -> %d kept (%d non-IE, %d old, %d total available)",
             keyword, len(out), dropped_region, dropped_age,
             search.get("result_count", 0))
    return out
