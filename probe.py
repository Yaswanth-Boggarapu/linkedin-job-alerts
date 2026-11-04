"""What hiring signals does LinkedIn's guest job page actually expose?

enrich.py already fetches this page for every shortlisted job, so anything
visible here is free: no extra requests, no extra rate-limit exposure.
The question is only what is in the markup.

Writes probe-result.md so the findings can be read from the repo.
"""

import json
import re
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
H = {"user-agent": UA, "accept-language": "en-IE,en;q=0.9"}

OUT = []
def say(*p):
    line = " ".join(str(x) for x in p)
    print(line)
    OUT.append(line)


def job_ids(n=6):
    """Pull real Irish job ids off the guest search endpoint."""
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
           "?keywords=data%20analyst&location=Ireland&start=0")
    r = requests.get(url, headers=H, timeout=25)
    ids = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', r.text)
    if not ids:
        ids = re.findall(r'/jobs/view/[^"?]*?-(\d{8,})', r.text)
    say(f"- search HTTP {r.status_code}, {len(r.text)} bytes, {len(ids)} ids found")
    return ids[:n]


# Every signal worth having, as a labelled pattern. Reported present/absent
# per job so we learn which are reliable rather than which exist once.
PATTERNS = {
    "applicants":      r'num-applicants__caption[^>]*>\s*([^<]+?)\s*<',
    "posted_ago":      r'posted-time-ago__text[^>]*>\s*([^<]+?)\s*<',
    "salary":          r'(?:compensation__salary|salary)[^>]*>\s*([^<]{3,60}?)\s*<',
    "benefits":        r'benefits__benefit[^>]*>\s*([^<]+?)\s*<',
    "poster_name":     r'base-main-card__title[^>]*>\s*([^<]+?)\s*<',
    "poster_headline": r'base-main-card__subtitle[^>]*>\s*([^<]+?)\s*<',
    "message_recruit": r'(message-the-recruiter|hiring-team|poster-info)',
    "easy_apply":      r'(easy-apply|easyApply)',
    "actively_hiring": r'(actively[- ]?hiring|Actively recruiting)',
    "applies_closed":  r'(no longer accepting applications|closed)',
}

CRITERIA = re.compile(
    r'criteria__subheader[^>]*>\s*([^<]+?)\s*</h3>\s*'
    r'<span[^>]*criteria__text[^>]*>\s*([^<]+?)\s*</span>', re.S | re.I)


say("# LinkedIn guest page: available hiring signals\n")

ids = job_ids()
if not ids:
    say("\n**No job ids returned.** The guest search endpoint may be blocking "
        "this runner IP; nothing further can be probed.")
else:
    found = {k: 0 for k in PATTERNS}
    criteria_seen = {}
    sample_html = ""

    for i, jid in enumerate(ids):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}"
        try:
            r = requests.get(url, headers=H, timeout=25)
        except Exception as exc:
            say(f"- job {jid}: FAILED {type(exc).__name__}")
            continue
        html = r.text
        if i == 0:
            sample_html = html
        say(f"\n### job {jid} (HTTP {r.status_code}, {len(html)} bytes)")

        for label, pat in PATTERNS.items():
            m = re.search(pat, html, re.I | re.S)
            if m:
                found[label] += 1
                val = (m.group(1) if m.lastindex else m.group(0))[:70]
                say(f"  - {label:16} {val!r}")

        for key, val in CRITERIA.findall(html):
            criteria_seen.setdefault(key.strip(), set()).add(val.strip()[:40])

        time.sleep(2)

    say("\n## Reliability across %d jobs\n" % len(ids))
    say("| signal | present in |")
    say("| --- | --- |")
    for label, count in sorted(found.items(), key=lambda kv: -kv[1]):
        say(f"| {label} | {count}/{len(ids)} |")

    say("\n## criteria blocks seen\n```")
    for key, vals in criteria_seen.items():
        say(f"{key:22} {sorted(vals)[:4]}")
    say("```")

    # Anything applicant- or hiring-shaped we did not anticipate.
    say("\n## nearby 'applicant' / 'hiring' markup in the first job\n```")
    for m in re.finditer(r'[^>]{0,90}(applicant|hiring|recruiter)[^<]{0,90}',
                         sample_html, re.I):
        chunk = " ".join(m.group(0).split())
        if len(chunk) > 12:
            say(chunk[:150])
    say("```")

open("probe-result.md", "w").write("\n".join(OUT))
