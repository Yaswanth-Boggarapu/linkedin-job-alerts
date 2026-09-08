"""The dedupe rules are the load-bearing logic, so they get the most tests."""
import json
from datetime import date, timedelta

import pytest

import seen_store


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(seen_store, "STATE_PATH", tmp_path / "seen.json")
    return {"jobs": {}, "content": {}}


def job(site="linkedin", jid="1", title="ML Engineer",
        company="Stripe", location="Dublin, Ireland"):
    return {"site": site, "id": jid, "title": title,
            "company": company, "location": location}


def test_new_job_is_reported(state):
    fresh, stats = seen_store.filter_new([job()], state)
    assert len(fresh) == 1
    assert stats["new"] == 1


def test_same_id_twice_is_suppressed(state):
    seen_store.filter_new([job()], state)
    fresh, stats = seen_store.filter_new([job()], state)
    assert fresh == []
    assert stats["dup_id"] == 1


def test_repost_under_new_id_is_suppressed(state):
    seen_store.filter_new([job(jid="1")], state)
    fresh, stats = seen_store.filter_new([job(jid="2")], state)
    assert fresh == []
    assert stats["dup_content"] == 1


def test_same_role_on_two_boards_reported_once(state):
    fresh, _ = seen_store.filter_new(
        [job(site="linkedin", jid="1"),
         job(site="indeed", jid="abc")], state)
    assert len(fresh) == 1


def test_company_suffixes_do_not_defeat_the_fingerprint():
    a = seen_store.content_key(job(company="Stripe"))
    b = seen_store.content_key(job(company="Stripe Ltd"))
    c = seen_store.content_key(job(company="Stripe Ireland"))
    assert a == b == c


@pytest.mark.parametrize("location", [
    "Dublin",
    "County Dublin",
    "Dublin, County Dublin, Ireland",
    "South Dublin",
    "Dublin City Centre",
])
def test_location_verbosity_does_not_defeat_the_fingerprint(location):
    """Boards phrase the same place very differently; all must collapse."""
    assert (seen_store.content_key(job(location=location))
            == seen_store.content_key(job(location="Dublin")))


def test_different_cities_stay_distinct():
    assert (seen_store.content_key(job(location="Cork"))
            != seen_store.content_key(job(location="Dublin")))


def test_old_repost_is_surfaced_and_flagged(state):
    stale = (date.today()
             - timedelta(days=seen_store.REPOST_AFTER_DAYS + 5)).isoformat()
    key = seen_store.content_key(job())
    state["content"][key] = stale

    fresh, stats = seen_store.filter_new([job(jid="99")], state)
    assert len(fresh) == 1
    assert fresh[0]["is_repost"] is True
    assert stats["repost"] == 1


def test_suppressed_sighting_refreshes_the_timestamp(state):
    old = (date.today() - timedelta(days=40)).isoformat()
    seen_store.filter_new([job()], state)
    state["jobs"]["linkedin:1"] = old

    seen_store.filter_new([job()], state)
    assert state["jobs"]["linkedin:1"] == date.today().isoformat()


def test_save_prunes_entries_past_the_cutoff(state, tmp_path):
    state["jobs"]["old:1"] = (
        date.today() - timedelta(days=seen_store.PRUNE_AFTER_DAYS + 1)).isoformat()
    state["jobs"]["new:1"] = date.today().isoformat()
    state["content"] = {}

    seen_store.save(state)
    written = json.loads((tmp_path / "seen.json").read_text())
    assert "old:1" not in written["jobs"]
    assert "new:1" in written["jobs"]
