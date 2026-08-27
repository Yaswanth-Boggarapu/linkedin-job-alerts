"""Work out how senior a role is, so fresher-friendly listings sort first.

Job boards don't expose a reliable structured experience field. LinkedIn's
job_level only arrives if you fetch every description (which is what gets you
rate limited), and experience_range is Naukri-only. So this infers from the
title first, then from any description text that happens to come back free.

Ranks sort ascending: 0 is the most junior, 9 means we couldn't tell.

Patterns are word-bounded on purpose. Plain substring matching turns
"AI Engineer" into a junior role because it contains "i ".
"""

import re

UNKNOWN = (9, "Not stated")

# Checked in order, first hit wins, so the most junior patterns come first:
# "Graduate Software Engineer" should read as graduate, not as engineer.
TIERS = [
    (0, "Graduate/Intern", r"""
        graduate | grad | intern | internship | placement | trainee |
        apprentice | entry[\s-]level | fresher | new\s+grad
    """),
    (1, "Junior", r"""
        junior | jr | associate | assistant | early\s+career | level\s*1
    """),
    (3, "Mid", r"""
        mid[\s-]level | intermediate | ii | level\s*2
    """),
    (5, "Senior", r"""
        senior | snr | sr | lead | principal | staff | head\s+of |
        director | manager | architect | iii | level\s*3
    """),
]

_COMPILED = [
    (rank, label, re.compile(r"\b(?:" + pattern + r")\b", re.I | re.X))
    for rank, label, pattern in TIERS
]

# "3+ years", "2-4 years experience", "minimum of 5 years"
_YEARS = re.compile(r"(\d{1,2})\s*(?:\+|plus|-\s*\d{1,2})?\s*years?", re.I)


def _from_years(text):
    """Lowest year count mentioned, when the text is talking about experience."""
    if not text or "experience" not in text.lower():
        return None

    found = [int(m.group(1)) for m in _YEARS.finditer(text)]
    found = [y for y in found if y <= 20]
    if not found:
        return None

    low = min(found)
    if low <= 1:
        return 0, "0-1 yrs"
    if low <= 2:
        return 2, "2 yrs"
    if low <= 4:
        return 3, str(low) + " yrs"
    return 5, str(low) + "+ yrs"


def classify(job):
    """Return (rank, label). Lower rank is more junior."""
    title = job.get("title") or ""

    for rank, label, rx in _COMPILED:
        if rx.search(title):
            return rank, label

    level = (job.get("job_level") or "").strip()
    if level:
        for rank, label, rx in _COMPILED:
            if rx.search(level):
                return rank, label

    years = _from_years(job.get("description"))
    if years:
        return years

    return UNKNOWN
