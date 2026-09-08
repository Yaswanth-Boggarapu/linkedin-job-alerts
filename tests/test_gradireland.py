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
