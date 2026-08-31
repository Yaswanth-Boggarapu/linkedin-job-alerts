"""What to search for. Everything here is safe to commit."""

import os

# Narrow queries beat one broad one: each stays well under LinkedIn's
# rate limit instead of paging deep enough to get blocked.
ROLES = [
    "machine learning engineer",
    "data engineer",
    "data scientist",
    "data analyst",
    "ai engineer",
]

# Open to anywhere in Ireland, so search the country rather than a city list.
# One location keeps the query count low enough to add more boards.
LOCATIONS = ["Ireland"]

# Only boards that actually respond from a GitHub Actions runner.
# Glassdoor returns 403 on its location autocomplete and Google Jobs is
# disabled in the EU, so both were dropped after probing rather than left
# in to burn ~40s a run returning nothing. They need a proxy layer.
SITES = ["linkedin", "indeed"]
COUNTRY = "Ireland"

RESULTS_PER_QUERY = 40
HOURS_OLD = 26          # slight overlap with the daily cron; dedupe handles it
DELAY_BETWEEN_QUERIES = 4

# Drop anything whose title matches these before it reaches you.
TITLE_EXCLUDE = [
    "senior", "staff", "principal", "lead", "manager", "director",
    "head of", "vp ", "architect",
]

# Secrets come from the environment.
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
DIGEST_TO = os.environ.get("DIGEST_TO", "")

WA_TOKEN = os.environ.get("WA_TOKEN", "")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID", "")
WA_TO = os.environ.get("WA_TO", "")
WA_TEMPLATE = os.environ.get("WA_TEMPLATE", "job_digest")
