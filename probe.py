"""Did glassdoor/gradireland fail today, or did dedupe suppress them?"""
import json, os, requests
import config, firecrawl_source, gradireland, seen_store
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

KEY=os.environ.get("FIRECRAWL_KEY","")
say("## source health\n")
say(f"- FIRECRAWL_KEY present: {bool(KEY)}")
try:
    c=requests.get("https://api.firecrawl.dev/v2/team/credit-usage",
        headers={"Authorization":f"Bearer {KEY}"},timeout=20).json()
    say(f"- credits remaining: {c.get('data',{}).get('remainingCredits')}")
except Exception as e:
    say(f"- credit lookup failed: {e}")

state = seen_store.load()
say(f"- state holds {len(state['jobs'])} job keys\n")

raw = {}
try:
    g = gradireland.fetch(config.GRADIRELAND_KEYWORDS)
    raw["gradireland"] = g
    say(f"- gradireland raw -> {len(g)}")
except Exception as e:
    say(f"- gradireland RAISED {type(e).__name__}: {e}")

for kw in config.FIRECRAWL_GLASSDOOR:
    try:
        j = firecrawl_source.fetch_glassdoor(kw)
        raw.setdefault("glassdoor", []).extend(j)
        say(f"- glassdoor/{kw} raw -> {len(j)}")
    except Exception as e:
        say(f"- glassdoor/{kw} RAISED {type(e).__name__}: {e}")

for kw in config.FIRECRAWL_JOBS_IE:
    try:
        j = firecrawl_source.fetch_jobs_ie(kw)
        raw.setdefault("jobs_ie", []).extend(j)
        say(f"- jobs.ie/{kw} raw -> {len(j)}")
    except Exception as e:
        say(f"- jobs.ie/{kw} RAISED {type(e).__name__}: {e}")

say("\n## how many are already in state\n")
for site, rows in raw.items():
    known = sum(1 for r in rows if f"{r['site']}:{r['id']}" in state["jobs"])
    say(f"- {site}: {len(rows)} fetched, {known} already seen, {len(rows)-known} would be new")

open("probe-result.md","w").write("\n".join(OUT))
