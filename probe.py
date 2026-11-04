"""Compare the two LinkedIn page forms using ids already known, so no search
request is needed. The previous attempt burned its search call on a throttled
IP and got nothing back.

Question: does the page enrich.py already fetches carry the applicant count,
or would adding it cost a second request per job?
"""
import re, time, requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
H = {"user-agent": UA, "accept-language": "en-IE,en;q=0.9"}
IDS = ["4486360165", "4482897502", "4477154425"]

OUT = []
def say(*p):
    l = " ".join(str(x) for x in p); print(l); OUT.append(l)

SIGNALS = {
    "applicants":   r'num-applicants__caption[^>]*>\s*([^<]+?)\s*<',
    "posted_ago":   r'posted-time-ago__text[^>]*>\s*([^<]+?)\s*<',
    "poster_name":  r'base-main-card__title[^>]*>\s*([^<]+?)\s*<',
    "enrich_desc":  r'<div class="(?:show-more-less-html__markup|description__text)[^"]*">',
    "enrich_crit":  (r'criteria__subheader">\s*Seniority level\s*</h3>\s*'
                     r'<span[^>]*criteria__text[^>]*>\s*([^<]+?)\s*</span>'),
    "any_criteria": r'criteria__subheader[^>]*>\s*([^<]+?)\s*</h3>',
}

say("# Which page carries which signal\n")
tally = {}
for jid in IDS:
    for label, url in (
        ("jobs/view  (enrich fetches this)", f"https://www.linkedin.com/jobs/view/{jid}"),
        ("guest api", f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}"),
    ):
        try:
            r = requests.get(url, headers=H, timeout=30, allow_redirects=True)
        except Exception as e:
            say(f"- {label}: FAILED {type(e).__name__}"); continue
        html, hits = r.text, []
        for name, pat in SIGNALS.items():
            if re.search(pat, html, re.I | re.S):
                hits.append(name)
                tally[(label, name)] = tally.get((label, name), 0) + 1
        say(f"- {jid} {label}: HTTP {r.status_code}, {len(html)}b")
        say(f"    matched: {hits or 'NOTHING'}")
        if r.status_code == 429 or "authwall" in r.url:
            say(f"    !! throttled or authwalled -> {r.url[:80]}")
        time.sleep(6)

say("\n## tally (out of %d jobs)\n" % len(IDS))
say("| page | signal | hits |")
say("| --- | --- | --- |")
for (label, name), c in sorted(tally.items()):
    say(f"| {label} | {name} | {c} |")

open("probe-result.md", "w").write("\n".join(OUT))
