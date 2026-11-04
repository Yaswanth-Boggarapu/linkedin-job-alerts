"""enrich.py fetches job["job_url"] (the /jobs/view/ page). The first probe
hit the /jobs-guest/jobs/api/jobPosting/ endpoint. If the signals live on
different pages, adding them is NOT free. Compare the two directly.

Also checks whether enrich's existing _CRITERIA regex matches anything at
all on the page it actually fetches.
"""
import re, time, requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
H = {"user-agent": UA, "accept-language": "en-IE,en;q=0.9"}
OUT = []
def say(*p):
    l = " ".join(str(x) for x in p); print(l); OUT.append(l)

SIGNALS = {
    "applicants":  r'num-applicants__caption[^>]*>\s*([^<]+?)\s*<',
    "posted_ago":  r'posted-time-ago__text[^>]*>\s*([^<]+?)\s*<',
    "poster_name": r'base-main-card__title[^>]*>\s*([^<]+?)\s*<',
    # exactly what enrich.py uses today
    "enrich_desc": r'<div class="(?:show-more-less-html__markup|description__text)[^"]*">',
    "enrich_crit": (r'criteria__subheader">\s*Seniority level\s*</h3>\s*'
                    r'<span[^>]*criteria__text[^>]*>\s*([^<]+?)\s*</span>'),
    # looser: any criteria block at all
    "any_criteria": r'criteria__subheader[^>]*>\s*([^<]+?)\s*</h3>',
}

search = requests.get(
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    "?keywords=data%20engineer&location=Ireland&start=0", headers=H, timeout=25)
ids = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', search.text)[:4]
say(f"# Which page carries which signal\n\n{len(ids)} ids\n")

tally = {}
for jid in ids:
    forms = {
        "jobs/view (what enrich fetches)": f"https://www.linkedin.com/jobs/view/{jid}",
        "jobs-guest api":                  f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}",
    }
    say(f"\n### job {jid}")
    for label, url in forms.items():
        try:
            r = requests.get(url, headers=H, timeout=25, allow_redirects=True)
        except Exception as e:
            say(f"- {label}: FAILED {type(e).__name__}"); continue
        html = r.text
        hits = []
        for name, pat in SIGNALS.items():
            m = re.search(pat, html, re.I | re.S)
            if m:
                hits.append(name)
                tally[(label, name)] = tally.get((label, name), 0) + 1
        say(f"- {label}: HTTP {r.status_code}, {len(html)}b, final={r.url.split('?')[0][:60]}")
        say(f"    matched: {hits or 'NOTHING'}")
        time.sleep(2)

say("\n## tally\n")
say("| page | signal | hits |")
say("| --- | --- | --- |")
for (label, name), c in sorted(tally.items()):
    say(f"| {label} | {name} | {c}/{len(ids)} |")

open("probe-result.md", "w").write("\n".join(OUT))
