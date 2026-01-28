from __future__ import annotations


def test_is_localhost():
    from app.security import is_localhost

    assert is_localhost("127.0.0.1") is True
    assert is_localhost("::1") is True
    assert is_localhost("testclient") is True
    assert is_localhost("8.8.8.8") is False

