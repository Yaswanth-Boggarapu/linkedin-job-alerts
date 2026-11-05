"""Hiring signals: parsing and display.

Every source exposes something the others do not, so these are gathered by
the adapters and formatted here in one place. Pure functions, so the whole
module is testable without a network.

What each source actually carries, measured on real Irish rows:
  LinkedIn     applicant count, posted-time, hiring contact (from the page
               enrich.py already fetches, so no extra requests)
  Indeed       direct apply link, company size, rating, job type
  gradireland  opportunity type, application deadline, direct apply link
  Glassdoor    company rating (already in the markdown we parse)
"""

import re
from datetime import datetime, timezone

# "45 applicants", "Over 200 applicants"
_APPLICANTS = re.compile(r"(over\s+)?([\d,]+)\s+applicant", re.I)

# "10 hours ago", "1 week ago", "3 weeks ago"
_AGO = re.compile(
    r"(\d+)\s*(minute|hour|day|week|month)s?\s+ago", re.I)

_AGO_HOURS = {"minute": 1 / 60, "hour": 1, "day": 24,
              "week": 168, "month": 730}


def parse_applicants(text):
    """-> (count, is_capped). LinkedIn gives exact numbers until it caps
    at 'Over 200', so the flag matters: 200 and 2000 look identical."""
    if not text:
        return None, False
    m = _APPLICANTS.search(text)
    if not m:
        return None, False
    try:
        return int(m.group(2).replace(",", "")), bool(m.group(1))
    except ValueError:
        return None, False


def parse_age_hours(text):
    """'10 hours ago' -> 10.0. Returns None when unparseable."""
    if not text:
        return None
    m = _AGO.search(text)
    if not m:
        return None
    return int(m.group(1)) * _AGO_HOURS[m.group(2).lower()]


def competition(count, capped, age_hours):
    """A short read on how contested a posting is.

    Raw applicant counts mislead: 120 applicants over three weeks is calmer
    than 45 in a morning. Rate per day is the comparable number.
    """
    if count is None:
        return ""
    if age_hours and age_hours >= 1:
        per_day = count / (age_hours / 24)
        if per_day >= 100:
            return "very busy"
        if per_day >= 30:
            return "busy"
        if per_day >= 8:
            return "steady"
        return "quiet"
    return "busy" if capped or count >= 100 else ""


def days_until(timestamp):
    """Whole days until a unix timestamp. Negative once past."""
    if not timestamp:
        return None
    try:
        when = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    except (ValueError, OSError, OverflowError, TypeError):
        return None
    return (when - datetime.now(timezone.utc)).days


def format_salary(value):
    """gradireland gives a dict; JobSpy gives separate min/max/currency."""
    if not value:
        return ""
    if isinstance(value, dict):
        lo, hi = value.get("lower"), value.get("upper")
        cur = {"EUR": "€", "GBP": "£", "USD": "$"}.get(value.get("currency"), "")
        if not lo:
            return ""
        lo, hi = str(lo), str(hi or "")
        if hi and hi != lo:
            return f"{cur}{_k(lo)}-{_k(hi)}"
        return f"{cur}{_k(lo)}"
    return str(value)


def _k(amount):
    try:
        n = int(float(amount))
    except (ValueError, TypeError):
        return str(amount)
    return f"{n // 1000}k" if n >= 1000 else str(n)


def badges(job):
    """Compact signals for one row, most decision-relevant first.

    Deliberately short: this shares a table cell, and a wall of metadata is
    as unreadable as none.
    """
    out = []

    count, capped = parse_applicants(job.get("applicants_text"))
    if count is not None:
        label = f"{count}+ applicants" if capped else f"{count} applicants"
        pace = competition(count, capped, parse_age_hours(job.get("posted_ago")))
        out.append(f"{label} ({pace})" if pace else label)

    if job.get("posted_ago"):
        out.append(job["posted_ago"])

    left = days_until(job.get("deadline"))
    if left is not None and left >= 0:
        out.append(f"closes in {left}d" if left else "closes today")

    salary = format_salary(job.get("salary"))
    if salary:
        out.append(salary)

    rating = job.get("company_rating")
    if rating:
        try:
            out.append(f"{float(rating):.1f}/5")
        except (ValueError, TypeError):
            pass

    for key in ("job_type", "company_size", "opportunity_type"):
        if job.get(key):
            out.append(str(job[key]))

    if job.get("hiring_contact"):
        out.append(f"via {job['hiring_contact']}")

    return out
