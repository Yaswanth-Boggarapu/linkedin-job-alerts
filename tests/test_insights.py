import pytest

import insights


# ----------------------------------------------------------- applicants
def test_exact_applicant_count():
    assert insights.parse_applicants("45 applicants") == (45, False)


def test_capped_count_is_flagged():
    """'Over 200' hides whether it is 200 or 2000, so the flag matters."""
    assert insights.parse_applicants("Over 200 applicants") == (200, True)


def test_thousands_separator():
    assert insights.parse_applicants("1,200 applicants") == (1200, False)


@pytest.mark.parametrize("text", ["", None, "Be the first", "no numbers here"])
def test_unparseable_applicants(text):
    assert insights.parse_applicants(text) == (None, False)


# ------------------------------------------------------------ posted age
@pytest.mark.parametrize("text,hours", [
    ("10 hours ago", 10),
    ("1 day ago", 24),
    ("1 week ago", 168),
    ("3 weeks ago", 504),
    ("30 minutes ago", 0.5),
])
def test_age_parsing(text, hours):
    assert insights.parse_age_hours(text) == hours


def test_age_unparseable():
    assert insights.parse_age_hours("just now") is None


# ----------------------------------------------------------- competition
def test_rate_beats_raw_count():
    """45 in a morning is more contested than 125 over a week, even though
    the raw count is lower. Rate per day is the comparable figure."""
    fresh = insights.competition(45, False, 10)
    stale = insights.competition(125, False, 168)
    assert fresh == "very busy"
    assert stale == "steady"


def test_no_count_means_no_verdict():
    assert insights.competition(None, False, 10) == ""


def test_capped_without_age_still_reads_busy():
    assert insights.competition(200, True, None) == "busy"


# --------------------------------------------------------------- salary
def test_single_value_salary_is_not_shown_as_a_range():
    assert insights.format_salary(
        {"currency": "EUR", "lower": "35000", "upper": "35000"}) == "€35k"


def test_salary_range():
    assert insights.format_salary(
        {"currency": "EUR", "lower": "35000", "upper": "48000"}) == "€35k-48k"


def test_salary_absent():
    assert insights.format_salary(None) == ""
    assert insights.format_salary({"currency": "EUR"}) == ""


# ------------------------------------------------------------- deadline
def test_past_deadline_is_negative():
    assert insights.days_until(1) < 0


def test_garbage_deadline_does_not_raise():
    assert insights.days_until("not-a-timestamp") is None
    assert insights.days_until(None) is None


def test_expired_deadline_is_not_shown():
    assert not any("closes" in b for b in insights.badges({"deadline": 1}))


# --------------------------------------------------------------- badges
def test_badges_empty_for_a_bare_job():
    assert insights.badges({"title": "Data Analyst"}) == []


def test_badges_cover_every_source():
    out = insights.badges({
        "applicants_text": "45 applicants", "posted_ago": "10 hours ago",
        "company_rating": 3.3, "opportunity_type": "Graduate job",
        "job_type": "fulltime", "hiring_contact": "Susan Cox",
    })
    joined = " ".join(out)
    for expected in ("45 applicants", "very busy", "10 hours ago",
                     "3.3/5", "Graduate job", "fulltime", "via Susan Cox"):
        assert expected in joined


def test_bad_rating_is_skipped_not_fatal():
    assert insights.badges({"company_rating": "n/a"}) == []
