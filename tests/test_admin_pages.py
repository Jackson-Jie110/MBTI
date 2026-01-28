from __future__ import annotations


def test_admin_requires_login_when_configured(client, monkeypatch):
    monkeypatch.setenv("MBTI_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("MBTI_ADMIN_PASSWORD", "pass")

    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers.get("location", "").startswith("/admin/login")
