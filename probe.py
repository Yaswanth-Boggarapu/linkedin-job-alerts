"""Last attempt at jobs.ie: full content + wait for JS listings to render."""
import json, os, re, requests
KEY=os.environ["FIRECRAWL_KEY"]; API="https://api.firecrawl.dev/v2/scrape"
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

def try_scrape(label, url, **opts):
    body={"url":url,"formats":["markdown"],"timeout":90000}
    body.update(opts)
    try:
        r=requests.post(API,headers={"Authorization":f"Bearer {KEY}",
            "Content-Type":"application/json"},json=body,timeout=140)
        d=r.json()
        md=(d.get("data") or {}).get("markdown") or ""
        say(f"### {label}\n- success={d.get('success')} chars={len(md)}")
        if not d.get("success"):
            say(f"- error: {str(d.get('error'))[:200]}"); return
        # individual postings usually carry a numeric id in the path
        cand=re.findall(r'\[([^\]]{6,110})\]\((https://www\.jobs\.ie/[^\)]*?/\d{5,}[^\)]*)\)', md)
        say(f"- links with a long numeric id: {len(cand)}")
        for t,u in cand[:5]: say(f"    {t[:55]!r} -> {u[:85]}")
        if not cand:
            from collections import Counter
            shapes=Counter(re.sub(r'\d+','N',u.replace('https://www.jobs.ie','')).split('?')[0][:50]
                           for _,u in re.findall(r'\[([^\]]+)\]\((https://www\.jobs\.ie[^\)]+)\)', md))
            say(f"- shapes: {shapes.most_common(8)}")
    except Exception as e:
        say(f"### {label}\n- FAILED {type(e).__name__}: {e}")
    say("")

try_scrape("full content, no main-only", "https://www.jobs.ie/jobs/data",
           onlyMainContent=False)
try_scrape("wait 6s for render", "https://www.jobs.ie/jobs/data",
           onlyMainContent=False, waitFor=6000)
try_scrape("dublin facet, waited", "https://www.jobs.ie/jobs/data/in-dublin",
           onlyMainContent=False, waitFor=6000)

open("probe-result.md","w").write("\n".join(OUT))
