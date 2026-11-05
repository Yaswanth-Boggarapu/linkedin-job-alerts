"""Which of JobSpy's 34 fields does each source actually fill, and what do
gradireland and Glassdoor expose beyond what the adapters currently keep?

scan.py keeps 9 fields. The rest are discarded without anyone checking
whether they held anything. This measures fill rate on real rows.
"""
import json, os, re, time
import pandas as pd
import requests
from jobspy import scrape_jobs

OUT = []
def say(*p):
    l = " ".join(str(x) for x in p); print(l); OUT.append(l)

KEPT = {"site","id","title","company","location","job_url","date_posted",
        "job_level","description"}

say("# What the other sources expose\n")

# ---------------------------------------------------------- JobSpy sources
for site, kw in (("indeed", "data analyst"), ("linkedin", "data analyst")):
    say(f"\n## {site}\n")
    try:
        df = scrape_jobs(site_name=[site], search_term=kw, location="Ireland",
                         results_wanted=15, hours_old=72,
                         country_indeed="Ireland", verbose=0)
    except Exception as exc:
        say(f"- FAILED {type(exc).__name__}: {str(exc)[:120]}")
        continue
    if df is None or df.empty:
        say("- no rows returned (throttled or nothing matching)")
        continue

    say(f"- {len(df)} rows\n")
    say("| field | filled | sample | currently kept |")
    say("| --- | --- | --- | --- |")
    for col in df.columns:
        filled = int(df[col].notna().sum())
        if filled == 0:
            continue
        sample = ""
        nz = df[col].dropna()
        if len(nz):
            sample = str(nz.iloc[0])[:45].replace("|", "/").replace("\n", " ")
        mark = "yes" if col in KEPT else "**NO**"
        say(f"| {col} | {filled}/{len(df)} | {sample} | {mark} |")
    time.sleep(5)

# ------------------------------------------------------------ gradireland
say("\n## gradireland (full document fields)\n")
try:
    r = requests.post(
        "https://gradireland.com/ext/svc/inferno-search-service-1-0/search",
        headers={"accept": "application/json, text/plain, */*",
                 "content-type": "application/json",
                 "origin": "https://gradireland.com",
                 "referer": "https://gradireland.com/search/jobs",
                 "user-agent": "Mozilla/5.0"},
        json={"fields": None, "keys": ["data"], "groupBy": None,
              "conditionGroup": {"conjunction": "AND", "groups": [{
                  "conjunction": "OR",
                  "conditions": [{"name": "application_deadline_date",
                                  "value": ["0", "NOW"], "operator": "NOT BETWEEN"}],
                  "tags": ["facet:application_deadline_date"]}]},
              "facets": [], "sort": None,
              "conditions": [{"name": "type", "value": "opportunity", "operator": "="}],
              "limit": 5, "offset": 0, "includePromoted": False},
        timeout=30)
    docs = r.json()["search"]["documents"]
    KEEP_GI = {"nid", "title", "sourceOrganisationName", "path", "regions", "createdAt", "body"}
    say(f"- {len(docs)} docs\n")
    say("| field | filled | sample | currently kept |")
    say("| --- | --- | --- | --- |")
    for key in sorted({k for d in docs for k in d}):
        vals = [d.get(key) for d in docs if d.get(key) not in (None, "", [], {})]
        if not vals:
            continue
        s = str(vals[0])[:45].replace("|", "/").replace("\n", " ")
        mark = "yes" if key in KEEP_GI else "**NO**"
        say(f"| {key} | {len(vals)}/{len(docs)} | {s} | {mark} |")
except Exception as exc:
    say(f"- FAILED {type(exc).__name__}: {str(exc)[:150]}")

# -------------------------------------------------------------- Glassdoor
say("\n## Glassdoor (rating already in the markdown we parse?)\n")
key = os.environ.get("FIRECRAWL_KEY", "")
if not key:
    say("- no FIRECRAWL_KEY")
else:
    try:
        r = requests.post("https://api.firecrawl.dev/v2/scrape",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"url": "https://www.glassdoor.ie/Job/ireland-data-jobs-SRCH_IL.0,7_IN70_KO8,12.htm",
                  "formats": ["markdown"], "onlyMainContent": True, "timeout": 60000},
            timeout=120)
        md = (r.json().get("data") or {}).get("markdown") or ""
        say(f"- markdown {len(md)} chars")
        ratings = re.findall(r"^(\d\.\d)$", md, re.M)
        say(f"- standalone ratings found: {len(ratings)} -> {ratings[:8]}")
        for pat, label in ((r"(\d+[KkMm]?\+?\s*(?:reviews|Reviews))", "review counts"),
                           (r"(€\s?[\d,]+(?:\s?-\s?€?\s?[\d,]+)?(?:/yr|/hr|K)?)", "salary strings"),
                           (r"(Easy Apply)", "easy apply")):
            hits = re.findall(pat, md)
            say(f"- {label}: {len(hits)} -> {hits[:5]}")
    except Exception as exc:
        say(f"- FAILED {type(exc).__name__}: {str(exc)[:150]}")

open("probe-result.md", "w").write("\n".join(OUT))
