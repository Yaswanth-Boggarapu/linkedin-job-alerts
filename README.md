# linkedin-job-alerts

A daily job scan that runs itself on free infrastructure. Pulls new postings
from four sources, suppresses anything it has already reported, and emails a
digest sorted with the most junior roles first. Optional WhatsApp ping.

Named for LinkedIn because that is where it started; it now aggregates four
boards through three different access strategies.

## Sources, and why each is reached differently

| Source | Route | Why |
| --- | --- | --- |
| LinkedIn | JobSpy | Works directly. Most restrictive: rate limits near the 10th page from one IP. |
| Indeed | JobSpy | Works directly, effectively no rate limiting. |
| Glassdoor | Firecrawl | Returns **403** to GitHub Actions IPs. Needs a proxy layer. |
| gradireland | Direct JSON API | Client-rendered site, but its search XHR is a public unauthenticated endpoint. |
| jobs.ie | *disabled* | Read-times-out directly; its search pages are SEO facet pages with no listings in the HTML. |

The routing rule is **what the site needs, not which tool is nicest**. A JSON
endpoint beats a scrape; a scrape beats a proxied scrape; a proxied scrape
costs credits, so it is last.

### gradireland needed different assumptions entirely

Three things that were wrong when it was first modelled on LinkedIn:

- Its region values are `County Dublin`, not `Dublin`.
- Postings sit open for months. Of 209 sampled, **none** were under a day old
  and the median age was 83 days, so a 26-hour window matched nothing.
- Multi-word search keys are matched strictly: `data` returns 130 results,
  `data engineer` returns none.

So the adapter walks the whole live catalogue once and matches titles locally,
with no age filter at all. The API query already excludes postings past their
application deadline, and cross-run dedupe means nothing is sent twice.

## The dedupe is the interesting part

LinkedIn's "posted X hours ago" is coarse, so a job posted late in the day
lands inside both today's and tomorrow's window. Without state you get the
same listings every morning and stop reading the email by week two.

Three cases, handled differently:

| Case | Example | Behaviour |
| --- | --- | --- |
| Same listing, same ID | Yesterday's job still live | Suppressed |
| Same role, new ID | Closed and reposted next week | Suppressed |
| Same role, long gap | Reposted after a month | Surfaced, flagged `[repost]` |

`seen_store.py` keys on two things: the board's native job ID for exact
matches, and a normalised fingerprint of company + title + city for reposts.
The fingerprint also catches the same role appearing on two boards, which a
single-ID scheme would let through as two separate alerts.

Company names are normalised before hashing because the same employer appears
as "Stripe", "Stripe Ltd" and "Stripe Ireland". Locations are truncated to the
first two words so "Dublin" and "Dublin, County Dublin, Ireland" collapse.

Every sighting refreshes an entry's timestamp even when suppressed, so pruning
at 120 days only drops listings that have genuinely disappeared.

## Every run accounts for itself

An early version reported only what was new, so a broken scraper and a quiet
day looked identical. Now each run commits `last-run.json`:

```json
{
  "fetched": {"linkedin": 114, "indeed": 32, "glassdoor": 90, "gradireland": 6,
              "_dropped": {"by_title": 81, "dup_in_run": 49}},
  "dedupe": {"total": 112, "dup_id": 63, "dup_content": 1, "new": 48},
  "failures": []
}
```

Every job is traceable from fetch to inbox. The digest carries the same table,
and an email is sent even when nothing is new.

## Design constraints

Free tier throughout, which drives most decisions:

- **GitHub Actions, public repo** — unlimited minutes, no card on file.
  Scheduled runs are queued, not guaranteed: observed delays range from
  minutes to twelve hours. Free runners cannot promise a delivery time.
- **Shared runner IPs** — so blocking is expected, not exceptional. A failed
  query is logged and skipped; a morning where only Indeed responded is still
  a useful morning.
- **Firecrawl free tier** — 1,000 credits/month, one page per credit. Current
  usage is ~90/month, leaving headroom for a source that starts blocking.
- **State in the repo** — `seen.json` is committed each run. No database, and
  the commit history doubles as a log of the pipeline actually running.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Searches live in `config.py`. Credentials come from the environment.

| Secret | What |
| --- | --- |
| `SMTP_USER` / `SMTP_PASS` | Gmail address and app password |
| `DIGEST_TO` | Where the digest goes |
| `FIRECRAWL_KEY` | Firecrawl API key (Glassdoor) |
| `WA_TOKEN` / `WA_PHONE_ID` / `WA_TO` | WhatsApp Cloud API (optional) |

Email alone is enough to run; the rest degrade gracefully.

### WhatsApp notes

Meta's test number sends free to up to five verified recipients. Two things
that catch people out: the token on the API Setup panel expires in hours, so
anything scheduled needs a System User token; and template parameters cannot
contain newlines, so the WhatsApp message is a short summary by design.

## Layout

```
config.py             searches, exclusions, per-source settings
scan.py               orchestrates all sources, counts what each drops
gradireland.py        direct JSON API adapter
firecrawl_source.py   proxied scraping + markdown parsers
experience.py         infers seniority from title, then from year counts
seen_store.py         two-key cross-run dedupe
notify.py             email digest + per-source health table + WhatsApp
main.py               scan -> dedupe -> sort -> notify -> log
```

MIT.
