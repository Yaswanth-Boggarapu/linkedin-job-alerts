"""Firecrawl-backed sources for boards that block CI runners directly.

Glassdoor returns 403 to the GitHub Actions IP and jobs.ie read-times-out, so
both go through Firecrawl's proxy layer. One page costs one credit; the free
plan allows 1,000 a month, so a handful of searches a day is comfortable.

Firecrawl returns markdown, not job records, so each board needs its own
parser below.
"""

import logging
import os
import re
from datetime import date, timedelta

import requests

log = logging.getLogger(__name__)

API = "https://api.firecrawl.dev/v2/scrape"
KEY = os.environ.get("FIRECRAWL_KEY", "")

GLASSDOOR = "glassdoor"
JOBS_IE = "jobs_ie"


def _scrape(url, timeout_ms=60000):
    if not KEY:
        raise RuntimeError("FIRECRAWL_KEY not set")
    resp = requests.post(
        API,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"],
              "onlyMainContent": True, "timeout": timeout_ms},
        timeout=(timeout_ms / 1000) + 30,
    )
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"firecrawl {data.get('code') or resp.status_code}: "
                           f"{str(data.get('error'))[:120]}")
    return (data.get("data") or {}).get("markdown") or ""


# --------------------------------------------------------------- glassdoor
_GD_LINK = re.compile(
    r"\[([^\]]{4,140})\]\((https://www\.glassdoor\.[a-z.]+/job-listing/[^)]+)\)"
)
_AGE = re.compile(r"^(\d+)\s*d$", re.M)
_RATING = re.compile(r"^\d\.\d$")


def _clean_lines(chunk):
    """Non-empty markdown lines with images and bullets stripped."""
    out = []
    for raw in chunk.split("\n"):
        line = raw.strip().lstrip("-").strip()
        if not line or line.startswith("!["):
            continue
        out.append(line)
    return out


def _gd_company(before):
    """Company sits just above the rating, which sits just above the title."""
    lines = _clean_lines(before[-500:])
    for i in range(len(lines) - 1, -1, -1):
        if _RATING.match(lines[i]) and i:
            return lines[i - 1]
    return lines[-1] if lines else ""


def _gd_location(after):
    for line in _clean_lines(after[:300]):
        if line.lower().startswith(("discover more", "easy apply")):
            continue
        return line
    return "Ireland"


def parse_glassdoor(md):
    jobs, seen = [], set()
    for m in _GD_LINK.finditer(md):
        title, url = m.group(1).strip(), m.group(2)
        jid = re.search(r"jl=(\d+)", url)
        jid = jid.group(1) if jid else url[-24:]
        if jid in seen:
            continue
        seen.add(jid)

        tail = md[m.end():m.end() + 900]
        age = _AGE.search(tail)
        posted = ""
        if age:
            posted = str(date.today() - timedelta(days=int(age.group(1))))

        jobs.append({
            "site": GLASSDOOR,
            "id": jid,
            "title": title,
            "company": _gd_company(md[:m.start()]),
            "location": _gd_location(md[m.end():]),
            "job_url": url.split("?")[0],
            "date_posted": posted,
            "description": "",
        })
    return jobs


def fetch_glassdoor(keyword):
    slug = keyword.replace(" ", "-")
    url = (f"https://www.glassdoor.ie/Job/ireland-{slug}-jobs-"
           f"SRCH_IL.0,7_IN70_KO8,{8 + len(keyword)}.htm")
    md = _scrape(url)
    jobs = parse_glassdoor(md)
    log.info("glassdoor/%s -> %d", keyword, len(jobs))
    return jobs


# ------------------------------------------------------------------ jobs.ie
_IE_LINK = re.compile(
    r"\[([^\]]{6,140})\]\((https://www\.jobs\.ie/(?:job|jobs)/[^)]*-\d{4,}[^)]*)\)"
)


def parse_jobs_ie(md):
    jobs, seen = [], set()
    for m in _IE_LINK.finditer(md):
        title, url = m.group(1).strip(), m.group(2)
        if url in seen:
            continue
        seen.add(url)
        jid = re.search(r"(\d{5,})", url)
        after = _clean_lines(md[m.end():m.end() + 300])
        jobs.append({
            "site": JOBS_IE,
            "id": jid.group(1) if jid else url[-20:],
            "title": title,
            "company": after[0] if after else "",
            "location": after[1] if len(after) > 1 else "Ireland",
            "job_url": url.split("?")[0],
            "date_posted": "",
            "description": "",
        })
    return jobs


def fetch_jobs_ie(keyword):
    url = f"https://www.jobs.ie/jobs/{keyword.replace(' ', '-')}"
    md = _scrape(url, timeout_ms=75000)
    jobs = parse_jobs_ie(md)
    log.info("jobs.ie/%s -> %d", keyword, len(jobs))
    return jobs
