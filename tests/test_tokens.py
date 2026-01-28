from __future__ import annotations

from datetime import timedelta


def test_hash_token_stable_with_secret():
    from app.services.tokens import hash_token

    assert hash_token("abc", secret="k") == hash_token("abc", secret="k")
    assert hash_token("abc", secret="k") != hash_token("abc", secret="k2")


def test_expiry_from_choice():
    from app.services.tokens import expiry_from_choice

    assert expiry_from_choice("1d") == timedelta(days=1)
    assert expiry_from_choice("7d") == timedelta(days=7)
    assert expiry_from_choice("30d") == timedelta(days=30)
    assert expiry_from_choice("permanent") is None

