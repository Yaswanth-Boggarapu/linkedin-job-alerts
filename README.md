# linkedin-job-alerts

A daily job scan that runs itself. Pulls new postings from LinkedIn and Indeed,
suppresses anything it has already told me about, and sends what's left by email
and WhatsApp. Runs entirely on free infrastructure.

## Why the dedupe is the interesting part

LinkedIn's "posted X hours ago" is coarse, so a job posted late in the day lands
inside both today's and tomorrow's 24-hour window. Without state you get the same
listings every morning and stop reading the email by week two.

There are three cases and they need different handling:

| Case | Example | Behaviour |
| --- | --- | --- |
| Same listing, same ID | Yesterday's job still live | Suppressed |
| Same role, new ID | Closed and reposted next week | Suppressed |
| Same role, long gap | Reposted after a month | Surfaced, flagged `[repost]` |

So `seen_store.py` keys on two things: the board's native job ID for exact
matches, and a normalised fingerprint of company + title + city for reposts.
The fingerprint also catches the same role appearing on both LinkedIn and
Indeed, which a single-ID scheme would let through as two separate alerts.

Company names are normalised before hashing because the same employer appears as
"Stripe", "Stripe Ltd" and "Stripe Ireland" across postings. Locations are
truncated to the first two words so "Dublin" and "Dublin, County Dublin, Ireland"
collapse to one key.

Every sighting refreshes an entry's timestamp even when it's suppressed, so
pruning at 120 days only drops listings that have genuinely disappeared rather
than long-running ones.

## Design constraints

Free tier throughout, which drives most of the decisions:

- **GitHub Actions on a public repo** — unlimited minutes, no card on file
- **Shared runner IPs** — so LinkedIn rate limiting is expected, not exceptional.
  Queries are narrow (one role, one city) rather than deep-paged, spaced 4s
  apart, and a failed query is logged and skipped rather than aborting the run.
  A morning where only Indeed responded is still a useful morning.
- **State in the repo** — `seen.json` is committed back each run. No database,
  and the commit history doubles as a log of the pipeline actually running.
- **`linkedin_fetch_description=False`** — fetching descriptions costs one extra
  request per job, which is what actually triggers blocks. Titles and URLs are
  enough to decide whether to open something.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Configure searches in `config.py`. Credentials come from the environment.

### Secrets

Add under Settings → Secrets and variables → Actions:

| Secret | What |
| --- | --- |
| `SMTP_USER` | Gmail address |
| `SMTP_PASS` | Gmail app password, not the account password |
| `DIGEST_TO` | Where the digest goes |
| `WA_TOKEN` | Meta system user token (optional) |
| `WA_PHONE_ID` | Cloud API phone number ID (optional) |
| `WA_TO` | Recipient in international format (optional) |

Email alone is enough to run. WhatsApp is additive.

### WhatsApp notes

Meta's test number sends free to up to five verified recipients with no business
verification. Two things that catch people out:

- The token on the API Setup panel expires in hours. Generate a System User token
  in Business Settings for anything scheduled.
- Template parameters can't contain newlines, so the WhatsApp message is a short
  summary by design. The full list goes by email.

## Layout

```
config.py       searches and env wiring
scan.py         JobSpy queries, per-query failure isolation
seen_store.py   two-key cross-run dedupe
notify.py       email digest + WhatsApp ping
main.py         scan -> dedupe -> notify
```

MIT.
