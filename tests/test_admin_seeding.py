from __future__ import annotations


def _login_admin(client) -> None:
    login_page = client.get("/admin/login")
    assert login_page.status_code == 200

    csrf = client.cookies.get("csrf_token")
    assert csrf

    r = client.post(
        "/admin/login",
        data={"csrf_token": csrf, "username": "admin", "password": "pass", "next": "/admin/questions"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert client.cookies.get("admin_session")


def test_admin_questions_auto_seeds_when_empty(client, db, monkeypatch):
    from app.models import Question

    monkeypatch.setenv("MBTI_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("MBTI_ADMIN_PASSWORD", "pass")

    assert db.query(Question).count() == 0

    _login_admin(client)

    r = client.get("/admin/questions")
    assert r.status_code == 200

    assert db.query(Question).count() > 0
