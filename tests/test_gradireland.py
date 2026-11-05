import gradireland


def doc(regions, title="Graduate Data Analyst"):
    return {"nid": 1, "title": title, "sourceOrganisationName": "Aon",
            "path": "/jobs/x-1", "regions": regions,
            "createdAt": "2026-08-31T08:00:00Z"}


def test_counties_are_recognised_as_ireland():
    """The API says 'County Dublin', not 'Dublin'."""
    assert gradireland._in_ireland(doc(["County Dublin"]))
    assert gradireland._in_ireland(doc(["County Galway", "Europe"]))


def test_plain_ireland_is_recognised():
    assert gradireland._in_ireland(doc(["Ireland"]))


def test_uk_and_europe_are_excluded():
    assert not gradireland._in_ireland(doc(["England", "Europe"]))
    assert not gradireland._in_ireland(doc(["Europe"]))


def test_northern_ireland_excluded_by_default():
    """UK jurisdiction: needs UK right to work, not Irish."""
    assert not gradireland._in_ireland(doc(["Northern Ireland"]))


def test_normalise_builds_an_absolute_url():
    row = gradireland._normalise(doc(["County Cork"]))
    assert row["job_url"] == "https://gradireland.com/jobs/x-1"
    assert row["site"] == "gradireland"
    assert row["company"] == "Aon"


# ------------------------------------------------- employer name coverage
def test_company_prefers_the_direct_field():
    assert gradireland._company(
        {"sourceOrganisationName": "Dell Technologies"}) == "Dell Technologies"


def test_company_falls_back_to_the_organisation_object():
    """sourceOrganisationName is blank on roughly 3 in 10 documents; without
    this fallback those rows reached the inbox with no employer at all."""
    assert gradireland._company(
        {"sourceOrganisationName": "", "organisation": {"title": "Aon"}}) == "Aon"


def test_company_blank_when_neither_is_present():
    assert gradireland._company({"organisation": {}}) == ""


def test_location_prefers_the_plain_string():
    assert gradireland._location(
        {"location": "Dublin", "city": ["Cork"], "regions": ["Ireland"]}) == "Dublin"


def test_location_falls_back_through_city_then_regions():
    assert gradireland._location({"city": ["Cork"]}) == "Cork"
    assert gradireland._location({"regions": ["County Galway"]}) == "County Galway"
    assert gradireland._location({}) == "Ireland"


def test_apply_url_strips_tracking():
    assert gradireland._apply_url(
        {"applicationUrl": "https://jobs.aon.com/jobs/110698?utm_source=gradireland&x=1"}
    ) == "https://jobs.aon.com/jobs/110698"


def test_normalise_carries_the_new_signals():
    row = gradireland._normalise({
        "nid": 1, "title": "Graduate Data Scientist", "path": "/jobs/x-1",
        "organisation": {"title": "Sky"}, "regions": ["County Dublin"],
        "createdAt": "2026-10-08T09:14:16Z",
        "opportunityType": ["Graduate scheme"], "applicationDeadline": 1794441600,
        "salary": {"currency": "EUR", "lower": "35000", "upper": "35000"},
    })
    assert row["company"] == "Sky"
    assert row["opportunity_type"] == "Graduate scheme"
    assert row["deadline"] == 1794441600
