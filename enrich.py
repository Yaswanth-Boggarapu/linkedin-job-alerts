"""Post-dedupe enrichment.

Descriptions are deliberately not fetched during the scan: one extra request
per job is what triggers LinkedIn's rate limiting, and a scan touches a few
hundred jobs. But only a dozen or so survive dedupe, so enriching *those* is
cheap and safe.

Two jobs here:
  1. fill in the description, so experience inference stops saying "Not stated"
  2. drop links that are already dead, so the digest never points at a 404
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

import experience

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# LinkedIn's guest job page keeps the body in one of these two wrappers.
_DESC = re.compile(
    r'<div class="(?:show-more-less-html__markup|description__text)[^"]*">(.*?)</div>',
    re.S,
)
_CRITERIA = re.compile(
    r'criteria__subheader">\s*Seniority level\s*</h3>\s*'
    r'<span[^>]*criteria__text[^>]*>\s*([^<]+?)\s*</span>', re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _text(html):
    return _WS.sub(" ", _TAGS.sub(" ", html)).strip()


def _fetch_one(job, timeout):
    """Return the job with description and seniority filled in where possible."""
    url = job.get("job_url")
    if not url:
        return job
    try:
        resp = requests.get(url, headers={"user-agent": UA,
                                          "accept-language": "en-IE,en;q=0.9"},
                            timeout=timeout)
        if resp.status_code in (404, 410):
            job["_dead"] = True
            return job
        if resp.status_code != 200:
            return job

        html = resp.text
        body = _DESC.search(html)
        if body:
            job["description"] = _text(body.group(1))[:4000]

        level = _CRITERIA.search(html)
        if level:
            job["job_level"] = level.group(1)
    except Exception as exc:
        log.debug("enrich failed for %s: %s", url, exc)
    return job


def enrich(jobs, timeout=15, workers=4, pause=0.4):
    """Fill descriptions, drop dead links, re-classify experience.

    Returns (kept, stats). Failures are non-fatal: a job that could not be
    enriched keeps whatever it already had.
    """
    if not jobs:
        return jobs, {"enriched": 0, "dead": 0, "reclassified": 0}

    todo = [j for j in jobs if not j.get("description")]
    log.info("enriching %d of %d fresh jobs", len(todo), len(jobs))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda j: _fetch_one(j, timeout), todo))
        time.sleep(pause)

    kept, dead, reclassified, enriched = [], 0, 0, 0
    for job in jobs:
        if job.pop("_dead", False):
            dead += 1
            continue
        if job.get("description"):
            enriched += 1
            # A description often reveals seniority the title did not.
            if job.get("exp_rank", 9) == 9:
                rank, label = experience.classify(job)
                if rank != 9:
                    job["exp_rank"], job["exp_label"] = rank, label
                    reclassified += 1
        job.pop("description", None)
        job.pop("job_level", None)
        kept.append(job)

    stats = {"enriched": enriched, "dead": dead, "reclassified": reclassified}
    log.info("enrichment: %s", stats)
    return kept, stats
