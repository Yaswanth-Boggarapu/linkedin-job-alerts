## Field names (3 docs, result_count=130)

```
applicationDeadline                int    1794355200
applicationEmail                   str    campus@quantbot.com
applicationOpen                    bool   True
applicationUrl                     str    https://www.quantbot.com/careers/?gh_jid=4299858009
asyncContent                       bool   True
body                               str    <p>Quantbot Technologies is a leading global quantitative investment firm deploying system…
createdAt                          str    2026-08-14T08:31:07Z
educationProvider                  dict   {'asyncContent': True, 'thumbnailImage': None, 'featuredImage': None, 'headlineImage': Non…
featured                           bool   False
featuredImage                      NoneType None
femalePercentage                   str    
foundedYear                        str    
freeJob                            bool   True
graduateImage                      NoneType None
graduatePositions                  str    
headlineImage                      NoneType None
logo                               NoneType None
nid                                int    236011
organisation                       dict   {'asyncContent': True, 'thumbnailImage': None, 'featuredImage': None, 'headlineImage': Non…
path                               str    /jobs/data-trading-analyst-summer-internship-2027-london-236011
preregister                        bool   False
promoted                           bool   False
regions                            list   ['England', 'Europe']
salary                             dict   {'currency': 'EUR'}
sourceOrganisationName             str    Quantbot Technologies Ltd
thumbnailImage                     NoneType None
title                              str    Data Trading Analyst Summer Internship - 2027 [London]
type                               str    opportunity
updatedAt                          str    2026-08-26T13:12:39Z
uuid                               str    c4e4620a-d348-4a0f-ba55-11f2a75bc37f
```

## Second doc, body stripped
```json
{
  "type": "opportunity",
  "title": "Data and AI Engineer - Clear Strategy, Dun Laoghaire (Hybrid)",
  "path": "/jobs/data-and-ai-engineer-clear-strategy-dun-laoghaire-hybrid-221136",
  "nid": 221136,
  "uuid": "9b15a89e-e2e4-4dd6-8e55-324713b5d08d",
  "asyncContent": true,
  "featured": false,
  "promoted": false,
  "logo": null,
  "graduateImage": null,
  "organisation": {
    "asyncContent": true,
    "thumbnailImage": null,
    "featuredImage": null,
    "headlineImage": null,
    "logo": null,
    "femalePercentage": "",
    "foundedYear": "",
    "graduatePositions": ""
  },
  "educationProvider": {
    "asyncContent": true,
    "thumbnailImage": null,
    "featuredImage": null,
    "headlineImage": null,
    "logo": null
  },
  "salary": {
    "currency": "EUR"
  },
  "thumbnailImage": null,
  "featuredImage": null,
  "headlineImage": null,
  "applicationDeadline": 1788825600,
  "applicationUrl": "https://www.clearstrategy.ie/careers/data-it-engineer",
  "applicationEmail": "careers@clearstrategy.ie",
  "applicationOpen": true,
  "preregister": false,
  "sourceOrganisationName": "Clear Strategy",
  "femalePercentage": "",
  "foundedYear": "",
  "graduatePositions": "",
  "sectors": [
    "Engineering"
  ],
  "freeJob": true,
  "createdAt": "2026-03-12T16:47:51Z",
  "updatedAt": "2026-04-30T08:30:33Z"
}
```

- sort [{"field": "last_published", "direction": "DESC"}] -> HTTP 400, count=None

- sort [{"name": "last_published", "order": "DESC"}] -> HTTP 200, count=130