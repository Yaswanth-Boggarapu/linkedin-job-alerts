"""What do jobs.ie posting links actually look like?"""
import json, os, re, requests
KEY=os.environ["FIRECRAWL_KEY"]; API="https://api.firecrawl.dev/v2/scrape"
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

def scrape(url, ms=75000):
    r=requests.post(API,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"},
        json={"url":url,"formats":["markdown"],"onlyMainContent":True,"timeout":ms},timeout=ms/1000+30)
    return r.json()

d=scrape("https://www.jobs.ie/jobs/data")
md=(d.get("data") or {}).get("markdown") or ""
meta=(d.get("data") or {}).get("metadata") or {}
say(f"## jobs.ie/jobs/data\n- success={d.get('success')} status={meta.get('statusCode')} chars={len(md)}\n")

links=re.findall(r'\[([^\]]{3,120})\]\((https?://[^\)]+)\)', md)
say(f"- total links: {len(links)}")
from collections import Counter
pats=Counter()
for t,u in links:
    p=re.sub(r'\d+','N',u.replace("https://www.jobs.ie",""))
    pats[p.split('?')[0][:60]]+=1
say("\n- url shapes (top 25):\n```")
for p,c in pats.most_common(25): say(f"{c:4}  {p}")
say("```")

say("\n- first 1800 chars:\n```\n"+md[:1800]+"\n```")
open("probe-result.md","w").write("\n".join(OUT))
