"""Structure of a Glassdoor job card in Firecrawl markdown, plus jobs.ie URL hunt."""
import json, os, re, requests

KEY=os.environ["FIRECRAWL_KEY"]; API="https://api.firecrawl.dev/v2/scrape"
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

def scrape(url, **extra):
    body={"url":url,"formats":["markdown"],"onlyMainContent":True,"timeout":60000}
    body.update(extra)
    r=requests.post(API,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json"},json=body,timeout=120)
    return r.json()

say("## Glassdoor card structure\n")
d=scrape("https://www.glassdoor.ie/Job/ireland-data-jobs-SRCH_IL.0,7_IN70_KO8,12.htm")
md=(d.get("data") or {}).get("markdown") or ""
m=re.search(r'\[[^\]]+\]\(https://www\.glassdoor\.ie/job-listing/', md)
if m:
    start=max(0, m.start()-900)
    say("```\n"+md[start:m.start()+1600]+"\n```")
else:
    say("no job-listing link found; first 1200 chars:\n```\n"+md[:1200]+"\n```")

say("\n## jobs.ie URL candidates\n")
for url in ["https://www.jobs.ie/jobs/data",
            "https://www.jobs.ie/jobs/in-dublin",
            "https://www.jobs.ie/jobs?q=data&l=Dublin"]:
    try:
        r=scrape(url, timeout=75000)
        ok=r.get("success")
        meta=(r.get("data") or {}).get("metadata") or {}
        mk=(r.get("data") or {}).get("markdown") or ""
        say(f"- `{url}` -> success={ok} status={meta.get('statusCode')} "
            f"chars={len(mk)} title={meta.get('title')!r}")
        if ok and mk:
            jl=re.findall(r'\[([^\]]{6,80})\]\((https://www\.jobs\.ie/[^\)]*job[^\)]*)\)', mk)
            say(f"    job links: {len(jl)}; sample: {jl[:3]}")
    except Exception as e:
        say(f"- `{url}` -> {type(e).__name__}: {e}")

try:
    c=requests.get("https://api.firecrawl.dev/v2/team/credit-usage",
        headers={"Authorization":f"Bearer {KEY}"},timeout=20).json()
    say(f"\n- credits: {c.get('data',{}).get('remainingCredits')}")
except Exception: pass
open("probe-result.md","w").write("\n".join(OUT))
