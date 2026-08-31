"""What region values does gradireland actually use, and how fresh is its stock?"""
import json, requests
from collections import Counter
from datetime import datetime, timezone

URL="https://gradireland.com/ext/svc/inferno-search-service-1-0/search"
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

H={"accept":"application/json, text/plain, */*","content-type":"application/json",
   "origin":"https://gradireland.com","referer":"https://gradireland.com/search/jobs",
   "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36"}

def payload(kw, limit):
    return {"fields":None,"keys":[kw],"groupBy":None,
      "conditionGroup":{"conjunction":"AND","groups":[{"conjunction":"OR",
        "conditions":[{"name":"application_deadline_date","value":["0","NOW"],"operator":"NOT BETWEEN"}],
        "tags":["facet:application_deadline_date"]}]},
      "facets":[],"sort":None,
      "conditions":[{"name":"type","value":"opportunity","operator":"="}],
      "limit":limit,"offset":0,"includePromoted":False}

regions=Counter(); ages=[]
for kw in ["data","machine learning","engineer","analyst",""]:
    r=requests.post(URL,headers=H,json=payload(kw,60),timeout=30)
    docs=r.json()["search"]["documents"]
    say(f"- keyword {kw!r}: result_count={r.json()['search']['result_count']}, returned={len(docs)}")
    for d in docs:
        for reg in (d.get("regions") or []):
            regions[str(reg)]+=1
        c=d.get("createdAt")
        if c:
            try:
                age=(datetime.now(timezone.utc)-datetime.fromisoformat(c.replace("Z","+00:00"))).days
                ages.append(age)
            except Exception: pass

say("\n## distinct regions\n```")
for k,v in regions.most_common(40): say(f"{v:5}  {k}")
say("```")

say("\n## age of postings (days since createdAt)\n```")
say("count:", len(ages))
if ages:
    ages.sort()
    say("min:",ages[0]," median:",ages[len(ages)//2]," max:",ages[-1])
    say("posted within 1 day:", sum(1 for a in ages if a<=1))
    say("within 7 days:", sum(1 for a in ages if a<=7))
    say("within 30 days:", sum(1 for a in ages if a<=30))
say("```")
open("probe-result.md","w").write("\n".join(OUT))
