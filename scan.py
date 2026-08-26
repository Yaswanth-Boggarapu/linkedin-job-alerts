"""Run the configured queries through JobSpy and return a flat list of dicts.

Per-query failures are logged and skipped. LinkedIn rate-limiting is expected,
not exceptional: a run that only gets Indeed results is still a useful run.
"""

import logging
import time

import pandas as pd
from jobspy import scrape_jobs

import config

log = logging.getLogger(__name__)

KEEP = ["site", "id", "title", "company", "location", "job_url", "date_posted"]


def _excluded(title):
    low = (title or "").lower()
    return any(bad in low for bad in config.TITLE_EXCLUDE)


def _one(site, role, location):
    df = scrape_jobs(
        site_name=[site],
        search_term=role,
        location=location,
        results_wanted=config.RESULTS_PER_QUERY,
        hours_old=config.HOURS_OLD,
        country_indeed=config.COUNTRY_INDEED,
        linkedin_fetch_description=False,
        verbose=0,
    )
    if df is None or df.empty:
        return []
    for col in KEEP:
        if col not in df.columns:
            df[col] = None
    df = df[KEEP].where(pd.notnull(df[KEEP]), None)
    return df.to_dict("records")


def collect():
    jobs, failures = [], []

    for site in config.SITES:
        for role in config.ROLES:
            for location in config.LOCATIONS:
                label = f"{site}/{role}/{location}"
                try:
                    found = _one(site, role, location)
                    jobs.extend(found)
                    log.info("%s -> %d", label, len(found))
                except Exception as exc:
                    failures.append(label)
                    log.warning("%s failed: %s", label, exc)
                time.sleep(config.DELAY_BETWEEN_QUERIES)

    kept = []
    seen_in_run = set()
    for job in jobs:
        if _excluded(job.get("title")):
            continue
        key = f"{job.get('site')}:{job.get('id')}"
        if key in seen_in_run:
            continue
        seen_in_run.add(key)
        job["date_posted"] = str(job.get("date_posted") or "")
        kept.append(job)

    log.info("collected %d unique after filters (%d queries failed)",
             len(kept), len(failures))
    return kept, failures
