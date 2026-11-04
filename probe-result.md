# Which page carries which signal

- 4486360165 jobs/view  (enrich fetches this): HTTP 200, 267879b
    matched: ['applicants', 'posted_ago', 'poster_name', 'enrich_desc']
- 4486360165 guest api: HTTP 200, 29271b
    matched: ['applicants', 'posted_ago', 'enrich_desc']
- 4482897502 jobs/view  (enrich fetches this): HTTP 200, 285707b
    matched: ['applicants', 'posted_ago', 'poster_name', 'enrich_desc']
- 4482897502 guest api: HTTP 200, 35405b
    matched: ['applicants', 'posted_ago', 'poster_name', 'enrich_desc']
- 4477154425 jobs/view  (enrich fetches this): HTTP 200, 283199b
    matched: ['applicants', 'posted_ago', 'poster_name', 'enrich_desc']
- 4477154425 guest api: HTTP 200, 45244b
    matched: ['applicants', 'posted_ago', 'enrich_desc']

## tally (out of 3 jobs)

| page | signal | hits |
| --- | --- | --- |
| guest api | applicants | 3 |
| guest api | enrich_desc | 3 |
| guest api | posted_ago | 3 |
| guest api | poster_name | 1 |
| jobs/view  (enrich fetches this) | applicants | 3 |
| jobs/view  (enrich fetches this) | enrich_desc | 3 |
| jobs/view  (enrich fetches this) | posted_ago | 3 |
| jobs/view  (enrich fetches this) | poster_name | 3 |