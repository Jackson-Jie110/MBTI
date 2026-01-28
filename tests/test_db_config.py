from __future__ import annotations

import importlib

import sqlalchemy


def _reload_app_modules() -> None:
    import app.db
    import app.main
    import app.routes.admin
    import app.routes.public

    importlib.reload(app.db)
    importlib.reload(app.routes.public)
    importlib.reload(app.routes.admin)
    importlib.reload(app.main)


def test_db_normalizes_postgres_url_without_driver_injection(monkeypatch):
    calls: dict[str, object] = {}

    original_create_engine = sqlalchemy.create_engine

    def fake_create_engine(url, *args, **kwargs):
        calls["url"] = url
        calls["connect_args"] = kwargs.get("connect_args", {})

        class DummyEngine:
            pass

        return DummyEngine()

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setenv("MBTI_DATABASE_URL", "postgres://user:pass@localhost:5432/db")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.db

    importlib.reload(app.db)

    assert calls["url"] == "postgresql://user:pass@localhost:5432/db"
    assert calls["connect_args"] == {}

    monkeypatch.setattr(sqlalchemy, "create_engine", original_create_engine)
    monkeypatch.delenv("MBTI_DATABASE_URL", raising=False)

    _reload_app_modules()


def test_db_sets_sqlite_check_same_thread(monkeypatch):
    calls: dict[str, object] = {}

    original_create_engine = sqlalchemy.create_engine

    def fake_create_engine(url, *args, **kwargs):
        calls["url"] = url
        calls["connect_args"] = kwargs.get("connect_args", {})

        class DummyEngine:
            pass

        return DummyEngine()

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)
    monkeypatch.setenv("MBTI_DATABASE_URL", "sqlite:///./mbti.db")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.db

    importlib.reload(app.db)

    assert calls["url"] == "sqlite:///./mbti.db"
    assert calls["connect_args"] == {"check_same_thread": False}

    monkeypatch.setattr(sqlalchemy, "create_engine", original_create_engine)
    monkeypatch.delenv("MBTI_DATABASE_URL", raising=False)

    _reload_app_modules()
