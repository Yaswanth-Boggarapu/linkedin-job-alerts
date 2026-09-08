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

# gradireland has its own adapter rather than going through JobSpy.
USE_GRADIRELAND = True
# gradireland's search matches multi-word keys strictly, so "data engineer"
# returns almost nothing. The adapter walks the whole live catalogue instead
# and matches these against the title.
GRADIRELAND_KEYWORDS = [
    "data", "machine learning", "ai ", "artificial intelligence",
    "analyst", "analytics", "python", "software engineer",
    # It is a graduate board, so the programme words matter as much as the
    # role words. The catalogue walk is a fixed cost, so more terms are free.
    "graduate", "intern", "placement", "trainee",
    "quantitative", "research", "statistic", "modelling",
    "engineer", "developer", "scientist", "technology",
]
COUNTRY = "Ireland"

# Firecrawl-backed boards. One page = one credit; the free plan gives 1,000 a
# month, so this costs roughly 180/month and leaves plenty of headroom.
# Keep these single words: both sites use them as URL slugs.
FIRECRAWL_GLASSDOOR = ["data", "analytics", "machine-learning"]
# jobs.ie is off. Its /jobs/<term> pages are SEO landing pages: the markup
# holds location facets and company logos but no linked job titles, so there
# is nothing stable to parse. Left wired up in case that changes.
FIRECRAWL_JOBS_IE = []

RESULTS_PER_QUERY = 40
HOURS_OLD = 26          # slight overlap with the daily cron; dedupe handles it
DELAY_BETWEEN_QUERIES = 4

# Drop anything whose title matches these before it reaches you.
# Matched as whole words (see scan._EXCLUDE_RX), so "lead" no longer rejects
# "Leadership". "architect" was dropped: Data Architect is often a mid-level
# title in Ireland and worth seeing.
TITLE_EXCLUDE = [
    "senior", "snr", "staff", "principal", "lead", "manager",
    "director", "head", "vp",
]

# Secrets come from the environment.
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
DIGEST_TO = os.environ.get("DIGEST_TO", "")

WA_TOKEN = os.environ.get("WA_TOKEN", "")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID", "")
WA_TO = os.environ.get("WA_TO", "")
WA_TEMPLATE = os.environ.get("WA_TEMPLATE", "job_digest")

# Fetch descriptions for the handful of jobs that survive dedupe, rather than
# the few hundred fetched. Also drops links that already 404.
ENRICH_SHORTLIST = True
