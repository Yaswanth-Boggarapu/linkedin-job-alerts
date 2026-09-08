import notion_source


def test_disabled_without_credentials(monkeypatch):
    monkeypatch.setattr(notion_source, "TOKEN", "")
    monkeypatch.setattr(notion_source, "DB", "")
    assert not notion_source.enabled()
    assert notion_source.applied_keys() == set()


def test_url_match_ignores_query_and_trailing_slash():
    keys = {"https://linkedin.com/jobs/view/4012"}
    job = {"job_url": "https://linkedin.com/jobs/view/4012?ref=x", "id": "4012"}
    assert notion_source.already_applied(job, keys)


def test_numeric_id_match():
    """A hand-pasted tracker URL rarely matches the scraped one exactly,
    so the board's numeric id is the fallback."""
    keys = {"4012345678"}
    assert notion_source.already_applied(
        {"job_url": "https://elsewhere.example/x", "id": "4012345678"}, keys)


def test_short_ids_do_not_match_loosely():
    assert not notion_source.already_applied(
        {"job_url": "https://x.example/a", "id": "12"}, {"12"})


def test_no_keys_means_no_filtering():
    assert not notion_source.already_applied({"job_url": "x", "id": "1"}, set())
