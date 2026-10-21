import notify


def set_addrs(monkeypatch, sender, digest_to):
    monkeypatch.setattr(notify.config, "SMTP_USER", sender)
    monkeypatch.setattr(notify.config, "DIGEST_TO", digest_to)


def test_single_recipient(monkeypatch):
    set_addrs(monkeypatch, "me@x.com", "me@x.com")
    assert notify.recipients() == ["me@x.com"]


def test_sender_is_always_included(monkeypatch):
    """Dropping the sender from DIGEST_TO must not stop their own copy."""
    set_addrs(monkeypatch, "me@x.com", "a@x.com, b@x.com")
    assert notify.recipients() == ["me@x.com", "a@x.com", "b@x.com"]


def test_sender_listed_twice_is_not_duplicated(monkeypatch):
    """A duplicate would send the sender two copies of every digest."""
    set_addrs(monkeypatch, "me@x.com", "me@x.com, a@x.com")
    assert notify.recipients() == ["me@x.com", "a@x.com"]


def test_case_and_whitespace_are_normalised(monkeypatch):
    set_addrs(monkeypatch, "me@x.com", "  ME@X.com ,  a@x.com  ")
    assert notify.recipients() == ["me@x.com", "a@x.com"]


def test_empty_digest_to_still_reaches_the_sender(monkeypatch):
    set_addrs(monkeypatch, "me@x.com", "")
    assert notify.recipients() == ["me@x.com"]


def test_trailing_comma_is_ignored(monkeypatch):
    set_addrs(monkeypatch, "me@x.com", "a@x.com,")
    assert notify.recipients() == ["me@x.com", "a@x.com"]
