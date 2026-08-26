"""Cross-run dedupe for the daily job scan.

Two keys per job:
  job_key      site + native id      -> exact same listing
  content_key  company|title|city    -> same role reposted under a new id,
                                        and cross-board duplicates

State lives in seen.json, committed back to the repo each run.
"""

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

STATE_PATH = Path("seen.json")

REPOST_AFTER_DAYS = 30   # older than this -> surface again, flagged
PRUNE_AFTER_DAYS = 120   # drop stale entries so the file stays small

_WS = re.compile(r"\s+")
_NOISE = re.compile(r"\b(inc|ltd|limited|plc|llc|gmbh|group|ireland|eu)\b")


def _norm(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = _NOISE.sub(" ", text)
    return _WS.sub(" ", text).strip()


def content_key(job):
    """Stable across reposts and across job boards."""
    city = _norm(job.get("location", "")).split()[:2]
    raw = f"{_norm(job.get('company'))}|{_norm(job.get('title'))}|{' '.join(city)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def job_key(job):
    return f"{job.get('site')}:{job.get('id')}"


def load():
    if not STATE_PATH.exists():
        return {"jobs": {}, "content": {}}
    return json.loads(STATE_PATH.read_text())


def save(state):
    cutoff = (date.today() - timedelta(days=PRUNE_AFTER_DAYS)).isoformat()
    for bucket in ("jobs", "content"):
        state[bucket] = {
            k: v for k, v in state[bucket].items() if v >= cutoff
        }
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def filter_new(jobs, state):
    """Return (to_notify, stats). Mutates state with today's sightings.

    Each returned job gains an 'is_repost' flag so the digest can label it.
    """
    today = date.today().isoformat()
    out, stats = [], {"total": len(jobs), "dup_id": 0, "dup_content": 0, "repost": 0}

    for job in jobs:
        jk, ck = job_key(job), content_key(job)

        if jk in state["jobs"]:
            state["jobs"][jk] = today
            stats["dup_id"] += 1
            continue

        last_seen = state["content"].get(ck)
        is_repost = False

        if last_seen:
            gap = (date.today() - date.fromisoformat(last_seen)).days
            if gap < REPOST_AFTER_DAYS:
                # Same role, new listing id, but we told you recently.
                state["jobs"][jk] = today
                state["content"][ck] = today
                stats["dup_content"] += 1
                continue
            is_repost = True
            stats["repost"] += 1

        state["jobs"][jk] = today
        state["content"][ck] = today
        out.append({**job, "is_repost": is_repost})

    stats["new"] = len(out)
    return out, stats


if __name__ == "__main__":
    state = load()
    sample = [
        {"site": "linkedin", "id": "4012", "title": "ML Engineer",
         "company": "Stripe Ltd", "location": "Dublin, Ireland"},
        {"site": "linkedin", "id": "4012", "title": "ML Engineer",
         "company": "Stripe Ltd", "location": "Dublin, Ireland"},
        {"site": "indeed", "id": "aa91", "title": "ML  Engineer",
         "company": "Stripe", "location": "Dublin"},
    ]
    fresh, stats = filter_new(sample, state)
    print(stats)          # 3 in, 1 out: id dupe + cross-board dupe both caught
    save(state)
