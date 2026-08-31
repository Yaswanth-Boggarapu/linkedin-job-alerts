"""Probe the gradireland search API: does it work without cookies, and
what do the result fields look like? Writes findings to probe-result.md."""

import json
import requests

URL = "https://gradireland.com/ext/svc/inferno-search-service-1-0/search"
OUT = []


def say(*p):
    line = " ".join(str(x) for x in p)
    print(line)
    OUT.append(line)


def body(keyword, limit=5):
    return {
        "fields": None,
        "keys": [keyword],
        "groupBy": None,
        "conditionGroup": {
            "conjunction": "AND",
            "groups": [{
                "conjunction": "OR",
                "conditions": [{
                    "name": "application_deadline_date",
                    "value": ["0", "NOW"],
                    "operator": "NOT BETWEEN",
                }],
                "tags": ["facet:application_deadline_date"],
            }],
        },
        "facets": [],
        "sort": None,
        "conditions": [{"name": "type", "value": "opportunity", "operator": "="}],
        "limit": limit,
        "offset": 0,
        "includePromoted": False,
    }


HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://gradireland.com",
    "referer": "https://gradireland.com/search/jobs",
    "x-host": "users.gradireland.com",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
}

say("## gradireland search API\n")

# 1. no cookies at all
try:
    r = requests.post(URL, headers=HEADERS, json=body("data"), timeout=30)
    say(f"- no cookies -> HTTP {r.status_code}, {len(r.content)} bytes")
    if r.status_code == 200:
        data = r.json()
        say(f"- top-level keys: {list(data)[:12]}")
        say("```json")
        say(json.dumps(data, indent=2)[:2500])
        say("```")
except Exception as exc:
    say(f"- no cookies -> FAILED {type(exc).__name__}: {exc}")

# 2. without the x-host header, to see if it matters
try:
    h = {k: v for k, v in HEADERS.items() if k != "x-host"}
    r = requests.post(URL, headers=h, json=body("data"), timeout=30)
    say(f"\n- without x-host -> HTTP {r.status_code}")
except Exception as exc:
    say(f"\n- without x-host -> FAILED: {exc}")

open("probe-result.md", "w").write("\n".join(OUT))
