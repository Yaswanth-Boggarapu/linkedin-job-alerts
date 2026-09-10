"""Work out which ATS each target company uses.

Nearly every ATS exposes a public unauthenticated JSON board endpoint that the
company's own careers page calls. Finding the right host + slug once means the
watcher can poll a clean API instead of scraping careers pages.

Writes ats-map.json (found) and ats-unknown.md (needs manual lookup).
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

UA = {"user-agent": "Mozilla/5.0", "accept": "application/json"}

PROVIDERS = [
    ("greenhouse", "https://boards-api.greenhouse.io/v1/boards/{s}/jobs",
     lambda d: d.get("jobs")),
    ("lever", "https://api.lever.co/v0/postings/{s}?mode=json",
     lambda d: d if isinstance(d, list) else None),
    ("ashby", "https://api.ashbyhq.com/posting-api/job-board/{s}",
     lambda d: d.get("jobs")),
    ("smartrecruiters", "https://api.smartrecruiters.com/v1/companies/{s}/postings",
     lambda d: d.get("content")),
    ("workable", "https://apply.workable.com/api/v1/widget/accounts/{s}",
     lambda d: d.get("jobs")),
    ("recruitee", "https://{s}.recruitee.com/api/offers/",
     lambda d: d.get("offers")),
]

STRIP = re.compile(r"\((.*?)\)|ireland|dublin|operations|\bhq\b|company", re.I)


def slugs(name):
    base = STRIP.sub(" ", name)
    base = re.sub(r"[^a-z0-9 ]", " ", base.lower()).strip()
    base = re.sub(r"\s+", " ", base)
    if not base:
        base = re.sub(r"[^a-z0-9]", "", name.lower())
    words = base.split()
    out = ["".join(words), "-".join(words)]
    if len(words) > 1:
        out += [words[0]]
    seen, uniq = set(), []
    for s in out:
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq[:3]


def probe(company):
    name = company["company"]
    for slug in slugs(name):
        for provider, template, extract in PROVIDERS:
            url = template.format(s=slug)
            try:
                r = requests.get(url, headers=UA, timeout=12)
                if r.status_code != 200:
                    continue
                jobs = extract(r.json())
                if jobs is None:
                    continue
                return {**company, "ats": provider, "slug": slug,
                        "count": len(jobs), "url": url}
            except Exception:
                continue
            finally:
                time.sleep(0.05)
    return {**company, "ats": None}


companies = json.load(open("companies.json"))
with ThreadPoolExecutor(max_workers=12) as pool:
    results = list(pool.map(probe, companies))

found = [r for r in results if r["ats"]]
missing = [r for r in results if not r["ats"]]

json.dump(found, open("ats-map.json", "w"), indent=1, sort_keys=True)

lines = [f"# ATS discovery\n",
         f"Found **{len(found)} of {len(results)}** via public board APIs.\n",
         "## Found\n",
         "| Company | Tier | ATS | Slug | Live roles |",
         "| --- | --- | --- | --- | --- |"]
for r in sorted(found, key=lambda x: (-x["count"], x["company"])):
    lines.append(f"| {r['company']} | {r['tier'].split(' - ')[0]} | {r['ats']} "
                 f"| `{r['slug']}` | {r['count']} |")
lines += ["\n## Not found on a public board API\n",
          "These need their careers page checked by hand.\n",
          "| Company | Tier | Location |", "| --- | --- | --- |"]
for r in sorted(missing, key=lambda x: x["tier"]):
    lines.append(f"| {r['company']} | {r['tier'].split(' - ')[0]} | {r['location']} |")

open("ats-discovery.md", "w").write("\n".join(lines))
print(f"found {len(found)} / {len(results)}")
