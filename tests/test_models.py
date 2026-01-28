from __future__ import annotations

from pathlib import Path


def test_models_create_tables(tmp_path: Path):
    from sqlalchemy import create_engine, inspect

    from app.models import Base

    db_path = tmp_path / "t.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"questions", "tests", "test_items", "answers"} <= tables

