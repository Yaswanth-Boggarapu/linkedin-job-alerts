import firecrawl_source

GLASSDOOR_MD = """
- ![Health Service Executive Logo](https://media.glassdoor.com/x.png)

Health Service Executive

3.5

[Data Analyst, Grade VI](https://www.glassdoor.ie/job-listing/data-analyst-JV_KO0,12.htm?jl=1010234036171)

Kerry

In addition, the Disability Services Division will progress.

Discover more

12d

- ![Stripe Logo](https://media.glassdoor.com/y.png)

Stripe

4.2

[Graduate Data Engineer](https://www.glassdoor.ie/job-listing/graduate-JV_KO0,22.htm?jl=999)

Dublin

3d
"""


def test_parses_every_card():
    assert len(firecrawl_source.parse_glassdoor(GLASSDOOR_MD)) == 2


def test_company_is_taken_from_above_the_rating():
    rows = firecrawl_source.parse_glassdoor(GLASSDOOR_MD)
    assert rows[0]["company"] == "Health Service Executive"
    assert rows[1]["company"] == "Stripe"


def test_location_is_the_line_after_the_title():
    rows = firecrawl_source.parse_glassdoor(GLASSDOOR_MD)
    assert [r["location"] for r in rows] == ["Kerry", "Dublin"]


def test_id_comes_from_the_jl_parameter():
    rows = firecrawl_source.parse_glassdoor(GLASSDOOR_MD)
    assert rows[0]["id"] == "1010234036171"


def test_tracking_params_are_stripped_from_the_url():
    rows = firecrawl_source.parse_glassdoor(GLASSDOOR_MD)
    assert "?" not in rows[0]["job_url"]


def test_age_marker_becomes_a_date():
    rows = firecrawl_source.parse_glassdoor(GLASSDOOR_MD)
    assert rows[0]["date_posted"]
    assert rows[0]["date_posted"] < rows[1]["date_posted"]


def test_empty_markdown_is_not_an_error():
    assert firecrawl_source.parse_glassdoor("") == []
