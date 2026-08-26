"""What to search for. Everything here is safe to commit."""

import os

# Narrow queries beat one broad one: each stays well under LinkedIn's
# rate limit instead of paging deep enough to get blocked.
ROLES = [
    "machine learning engineer",
    "data engineer",
    "data scientist",
    "ai engineer",
]

LOCATIONS = [
    "Dublin, Ireland",
    "Cork, Ireland",
    "Galway, Ireland",
]

SITES = ["linkedin", "indeed"]
COUNTRY_INDEED = "Ireland"

RESULTS_PER_QUERY = 40
HOURS_OLD = 26          # slight overlap with the 24h cron; dedupe handles it
DELAY_BETWEEN_QUERIES = 4

# Drop anything whose title matches these before it reaches you.
TITLE_EXCLUDE = [
    "senior", "staff", "principal", "lead", "manager", "director",
    "head of", "vp ", "architect",
]

# Secrets come from the environment (GitHub Actions secrets locally: .env)
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
DIGEST_TO = os.environ.get("DIGEST_TO", "")

WA_TOKEN = os.environ.get("WA_TOKEN", "")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID", "")
WA_TO = os.environ.get("WA_TO", "")
WA_TEMPLATE = os.environ.get("WA_TEMPLATE", "job_digest")
