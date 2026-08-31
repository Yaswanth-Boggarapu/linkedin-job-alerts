
## Glassdoor

- `Ireland` (country as location) -> 0 rows
- `Dublin, Ireland` (city as location) -> 0 rows
- `Dublin` (bare city) -> 0 rows
- location autocomplete HTTP 403, body starts: 'Forbidden'

## jobs.ie

### https://www.jobs.ie/jobs?q=data
- FAILED: ReadTimeout: HTTPSConnectionPool(host='www.jobs.ie', port=443): Read timed out. (read timeout=25)
### https://www.jobs.ie/ShowResults.aspx?Keywords=data
- FAILED: ReadTimeout: HTTPSConnectionPool(host='www.jobs.ie', port=443): Read timed out. (read timeout=25)
### https://www.jobs.ie/
- FAILED: ReadTimeout: HTTPSConnectionPool(host='www.jobs.ie', port=443): Read timed out. (read timeout=25)