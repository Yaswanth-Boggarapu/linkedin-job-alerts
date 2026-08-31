"""Run the configured queries through JobSpy and return a flat list of dicts.

Per-query failures are logged and skipped. Rate limiting is expected, not
exceptional: a run that only gets two of four boards is still a useful run.
"""

import logging
import time

import pandas as pd
from jobspy import scrape_jobs

import config
import experience
import gradireland

log = logging.getLogger(__name__)

KEEP = ["site", "id", "title", "company", "location", "job_url",
        "date_posted", "job_level", "description"]


def _excluded(title):
    low = (title or "").lower()
    return any(bad in low for bad in config.TITLE_EXCLUDE)


def _one(site, role, location):
    kwargs = dict(
        site_name=[site],
        search_term=role,
        location=location,
        results_wanted=config.RESULTS_PER_QUERY,
        hours_old=config.HOURS_OLD,
        country_indeed=config.COUNTRY,
        linkedin_fetch_description=False,
        verbose=0,
    )
    # Google's scraper wants a natural-language query rather than a term
    # plus a location field.
    if site == "google":
        kwargs["google_search_term"] = f"{role} jobs in {location}"

    df = scrape_jobs(**kwargs)
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
                label = f"{site}/{role}"
                try:
                    found = _one(site, role, location)
                    jobs.extend(found)
                    log.info("%s -> %d", label, len(found))
                except Exception as exc:
                    failures.append(label)
                    log.warning("%s failed: %s", label, exc)
                time.sleep(config.DELAY_BETWEEN_QUERIES)

    # gradireland is not a JobSpy board: it has its own public JSON API.
    if config.USE_GRADIRELAND:
        for role in config.ROLES:
            try:
                found = gradireland.fetch(role, hours_old=config.HOURS_OLD)
                jobs.extend(found)
                log.info("gradireland/%s -> %d", role, len(found))
            except Exception as exc:
                failures.append(f"gradireland/{role}")
                log.warning("gradireland/%s failed: %s", role, exc)
            time.sleep(config.DELAY_BETWEEN_QUERIES)

    kept, seen_in_run = [], set()
    for job in jobs:
        if _excluded(job.get("title")):
            continue
        key = f"{job.get('site')}:{job.get('id')}"
        if key in seen_in_run:
            continue
        seen_in_run.add(key)

        rank, label = experience.classify(job)
        job["exp_rank"] = rank
        job["exp_label"] = label
        job["date_posted"] = str(job.get("date_posted") or "")
        job.pop("description", None)   # only needed for classification
        job.pop("job_level", None)
        kept.append(job)

    log.info("collected %d unique after filters (%d queries failed)",
             len(kept), len(failures))
    return kept, failures
