from __future__ import annotations


def _seed_questions(db, per_dim: int):
    from app.models import Question

    pole = {"EI": "E", "SN": "S", "TF": "T", "JP": "J"}
    for dim in ["EI", "SN", "TF", "JP"]:
        for i in range(per_dim):
            db.add(
                Question(
                    dimension=dim,
                    agree_pole=pole[dim],
                    text=f"[{dim}] 测试题 {i + 1}",
                    is_active=True,
                    source="test",
                )
            )
    db.commit()


def test_home_page_has_no_cross_device_resume_section(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "跨设备续测" not in r.text


def test_cross_device_resume_endpoints_removed(client, db):
    _seed_questions(db, per_dim=5)

    home = client.get("/")
    assert home.status_code == 200
    csrf = client.cookies.get("csrf_token")
    assert csrf

    start = client.post(
        "/start",
        data={"mode": "20", "resume_expiry": "7d", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert start.status_code == 303

    assert client.cookies.get("resume_token") is None
    assert client.cookies.get("resume_code") is None

    r1 = client.get("/resume/anything", follow_redirects=False)
    assert r1.status_code == 404

    r2 = client.post(
        "/resume",
        data={"csrf_token": csrf, "resume_code": "ABCD1234"},
        follow_redirects=False,
    )
    assert r2.status_code == 404
