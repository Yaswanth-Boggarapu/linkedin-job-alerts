"""One-off diagnostic. Writes findings to probe-result.md so they can be read
from the repo, since Actions logs aren't reachable from where this was written.

Covers two questions:
  1. Why does Glassdoor return nothing?
  2. Is jobs.ie server-rendered, JSON-backed, or JS-only?
"""

import json
import re
import traceback

import requests

OUT = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    OUT.append(line)


# ---------------------------------------------------------------- glassdoor
def glassdoor():
    say("\n## Glassdoor\n")
    from jobspy import scrape_jobs

    attempts = [
        ("Ireland", "country as location"),
        ("Dublin, Ireland", "city as location"),
        ("Dublin", "bare city"),
    ]
    for loc, label in attempts:
        try:
            df = scrape_jobs(
                site_name=["glassdoor"],
                search_term="data analyst",
                location=loc,
                results_wanted=10,
                hours_old=72,
                country_indeed="Ireland",
                verbose=2,
            )
            n = 0 if df is None else len(df)
            say(f"- `{loc}` ({label}) -> {n} rows")
            if n:
                say("  columns:", ", ".join(list(df.columns)[:8]))
        except Exception as exc:
            say(f"- `{loc}` ({label}) -> EXCEPTION {type(exc).__name__}: {exc}")

    # Is the location autocomplete itself working?
    try:
        r = requests.get(
            "https://www.glassdoor.ie/findPopularLocationAjax.htm"
            "?maxLocationsToReturn=10&term=Ireland",
            headers={"user-agent": "Mozilla/5.0"}, timeout=20,
        )
        say(f"- location autocomplete HTTP {r.status_code}, body starts: {r.text[:160]!r}")
    except Exception as exc:
        say(f"- location autocomplete failed: {exc}")


# ------------------------------------------------------------------ jobs.ie
CANDIDATES = [
    "https://www.jobs.ie/jobs?q=data",
    "https://www.jobs.ie/ShowResults.aspx?Keywords=data",
    "https://www.jobs.ie/",
]


def jobs_ie():
    say("\n## jobs.ie\n")
    for url in CANDIDATES:
        try:
            r = requests.get(
                url,
                headers={
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/125.0 Safari/537.36",
                    "accept-language": "en-IE,en;q=0.9",
                },
                timeout=25,
            )
            body = r.text
            say(f"### {url}")
            say(f"- HTTP {r.status_code}, {len(body)} bytes, server={r.headers.get('server')!r}")
            say(f"- cloudflare markers: "
                f"{'cf-ray' in {k.lower() for k in r.headers} or 'cloudflare' in body[:3000].lower()}")

            ld = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                            body, re.S)
            types = []
            for blob in ld:
                try:
                    data = json.loads(blob)
                except Exception:
                    continue
                for item in (data if isinstance(data, list) else [data]):
                    if isinstance(item, dict):
                        types.append(item.get("@type"))
            say(f"- JSON-LD blocks: {len(ld)}, types: {types}")
            say(f"- contains 'JobPosting': {'JobPosting' in body}")

            # crude check for server-rendered listings
            hits = len(re.findall(r'job[-_]?(?:title|card|result)', body, re.I))
            say(f"- job-ish markup hits: {hits}")

            # any obvious api endpoints referenced
            apis = set(re.findall(r'["\'](/api/[a-z0-9/_-]+)["\']', body, re.I))
            say(f"- /api/ paths referenced: {sorted(apis)[:8]}")
        except Exception as exc:
            say(f"### {url}\n- FAILED: {type(exc).__name__}: {exc}")


for fn in (glassdoor, jobs_ie):
    try:
        fn()
    except Exception:
        say("```\n" + traceback.format_exc() + "```")

open("probe-result.md", "w").write("\n".join(OUT))
