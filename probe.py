"""Second pass: what fields does a gradireland document actually have?"""
import json, requests

URL = "https://gradireland.com/ext/svc/inferno-search-service-1-0/search"
OUT = []
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

H = {"accept":"application/json, text/plain, */*",
     "content-type":"application/json",
     "origin":"https://gradireland.com",
     "referer":"https://gradireland.com/search/jobs",
     "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36"}

def payload(kw, limit=3, sort=None):
    return {"fields":None,"keys":[kw],"groupBy":None,
        "conditionGroup":{"conjunction":"AND","groups":[{"conjunction":"OR",
            "conditions":[{"name":"application_deadline_date","value":["0","NOW"],
                           "operator":"NOT BETWEEN"}],
            "tags":["facet:application_deadline_date"]}]},
        "facets":[],"sort":sort,
        "conditions":[{"name":"type","value":"opportunity","operator":"="}],
        "limit":limit,"offset":0,"includePromoted":False}

r = requests.post(URL, headers=H, json=payload("data"), timeout=30)
docs = r.json()["search"]["documents"]
say(f"## Field names ({len(docs)} docs, result_count={r.json()['search']['result_count']})\n")
say("```")
for k, v in sorted(docs[0].items()):
    prev = str(v)
    if len(prev) > 90:
        prev = prev[:90] + "…"
    say(f"{k:34} {type(v).__name__:6} {prev}")
say("```")

say("\n## Second doc, body stripped\n```json")
d2 = {k: v for k, v in docs[1].items() if k not in ("body", "description")}
say(json.dumps(d2, indent=2)[:2000])
say("```")

# does sorting by recency work?
for s in ([{"field":"last_published","direction":"DESC"}],
          [{"name":"last_published","order":"DESC"}]):
    try:
        rr = requests.post(URL, headers=H, json=payload("data", 2, s), timeout=30)
        say(f"\n- sort {json.dumps(s)} -> HTTP {rr.status_code}, "
            f"count={rr.json().get('search',{}).get('result_count')}")
    except Exception as e:
        say(f"\n- sort {json.dumps(s)} -> {type(e).__name__}: {e}")

open("probe-result.md","w").write("\n".join(OUT))
