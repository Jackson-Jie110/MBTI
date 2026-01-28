from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.models import Base, Question


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed MBTI questions into SQLite database.")
    parser.add_argument(
        "--db",
        default="sqlite:///./mbti.db",
        help="Database URL, default: sqlite:///./mbti.db",
    )
    parser.add_argument(
        "--file",
        default=str(PROJECT_ROOT / "app" / "data" / "seed_questions.json"),
        help="Seed JSON file path",
    )
    args = parser.parse_args()

    seed_path = Path(args.file)
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Seed file must be a JSON array.")

    engine = create_engine(
        args.db,
        connect_args={"check_same_thread": False} if str(args.db).startswith("sqlite") else {},
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as s:
        existing = set(
            s.execute(select(Question.dimension, Question.agree_pole, Question.text)).all()
        )
        inserted = 0
        for row in data:
            if not isinstance(row, dict):
                continue
            dim = str(row.get("dimension", "")).strip().upper()
            pole = str(row.get("agree_pole", "")).strip().upper()[:1]
            text = str(row.get("text", "")).strip()
            if not dim or not pole or not text:
                continue
            key = (dim, pole, text)
            if key in existing:
                continue
            s.add(
                Question(
                    dimension=dim,
                    agree_pole=pole,
                    text=text,
                    is_active=bool(row.get("is_active", True)),
                    source=str(row.get("source", "ai"))[:20],
                )
            )
            existing.add(key)
            inserted += 1
        s.commit()

    print(f"Inserted {inserted} questions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
