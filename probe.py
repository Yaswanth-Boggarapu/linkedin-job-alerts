"""Does the gradireland `organisation` object carry the employer name?

sourceOrganisationName is filled only 2/5, and it is what the adapter uses
for `company`, so most gradireland rows reach the inbox with no employer.
"""
import json, requests

OUT = []
def say(*p):
    l = " ".join(str(x) for x in p); print(l); OUT.append(l)

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
          "limit": 10, "offset": 0, "includePromoted": False},
    timeout=30)
docs = r.json()["search"]["documents"]
say(f"# gradireland employer name sources ({len(docs)} docs)\n")

say("| # | sourceOrganisationName | organisation keys | organisation.title |")
say("| --- | --- | --- | --- |")
for i, d in enumerate(docs):
    son = d.get("sourceOrganisationName") or "(empty)"
    org = d.get("organisation") or {}
    keys = ",".join(sorted(org)[:6]) if isinstance(org, dict) else type(org).__name__
    title = org.get("title") if isinstance(org, dict) else ""
    say(f"| {i} | {son[:28]} | {keys[:60]} | {str(title)[:28]} |")

say("\n## full organisation object, first doc\n```json")
say(json.dumps(docs[0].get("organisation"), indent=2)[:1200])
say("```")

say("\n## coverage\n")
for label, fn in (
    ("sourceOrganisationName", lambda d: d.get("sourceOrganisationName")),
    ("organisation.title", lambda d: (d.get("organisation") or {}).get("title")),
    ("organisation.name", lambda d: (d.get("organisation") or {}).get("name")),
    ("educationProvider.title", lambda d: (d.get("educationProvider") or {}).get("title")),
):
    n = sum(1 for d in docs if fn(d))
    say(f"- {label}: {n}/{len(docs)}")

# salary + deadline shapes, needed for the digest columns
say("\n## salary / deadline / opportunityType shapes\n```")
for d in docs[:5]:
    say(json.dumps({k: d.get(k) for k in
                    ("salary", "applicationDeadline", "opportunityType",
                     "city", "location", "applicationUrl")})[:300])
say("```")

open("probe-result.md", "w").write("\n".join(OUT))
