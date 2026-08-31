"""Can Firecrawl reach what the runner can't, and is the output parseable?

Tests jobs.ie (read-timed out from CI) and glassdoor.ie (403 from CI).
Reports credits used so we know the real cost per run.
"""
import json, os, re, requests

KEY = os.environ["FIRECRAWL_KEY"]
API = "https://api.firecrawl.dev/v2/scrape"
OUT = []
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

def credits():
    try:
        r = requests.get("https://api.firecrawl.dev/v2/team/credit-usage",
                         headers={"Authorization": f"Bearer {KEY}"}, timeout=20)
        return r.json()
    except Exception as e:
        return f"lookup failed: {e}"

say("## Firecrawl probe\n")
say(f"- credits before: {json.dumps(credits())[:200]}\n")

TARGETS = [
    ("jobs.ie search",   "https://www.jobs.ie/jobs?q=data"),
    ("jobs.ie home",     "https://www.jobs.ie/"),
    ("glassdoor.ie",     "https://www.glassdoor.ie/Job/ireland-data-jobs-SRCH_IL.0,7_IN70_KO8,12.htm"),
]

for label, url in TARGETS:
    say(f"### {label}\n`{url}`\n")
    try:
        r = requests.post(API,
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True,
                  "timeout": 45000},
            timeout=90)
        say(f"- HTTP {r.status_code}")
        data = r.json()
        if not data.get("success"):
            say(f"- not successful: {json.dumps(data)[:400]}")
            continue
        md = (data.get("data") or {}).get("markdown") or ""
        meta = (data.get("data") or {}).get("metadata") or {}
        say(f"- statusCode={meta.get('statusCode')}, markdown {len(md)} chars")
        say(f"- title: {meta.get('title')!r}")
        # how job-like is it?
        links = re.findall(r'\[([^\]]{5,90})\]\((https?://[^\)]+)\)', md)
        joby = [(t, u) for t, u in links if re.search(r'/job', u, re.I)]
        say(f"- links: {len(links)}, job-ish links: {len(joby)}")
        for t, u in joby[:6]:
            say(f"    - {t[:60]!r} -> {u[:80]}")
        say("\n- first 700 chars of markdown:\n```\n" + md[:700] + "\n```\n")
    except Exception as exc:
        say(f"- FAILED {type(exc).__name__}: {exc}\n")

say(f"\n- credits after: {json.dumps(credits())[:200]}")
open("probe-result.md","w").write("\n".join(OUT))
