from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Question


_DEFAULT_SEED_PATH = Path(__file__).resolve().parent / "data" / "seed_questions.json"


def seed_questions_if_empty(db: Session, *, seed_path: Path | None = None) -> int:
    has_any = db.execute(select(Question.id).limit(1)).first() is not None
    if has_any:
        return 0

    path = seed_path or _DEFAULT_SEED_PATH
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Seed data must be a JSON array.")

    inserted = 0
    for row in data:
        if not isinstance(row, dict):
            continue
        dim = str(row.get("dimension", "")).strip().upper()
        pole = str(row.get("agree_pole", "")).strip().upper()[:1]
        text = str(row.get("text", "")).strip()
        if not dim or not pole or not text:
            continue
        db.add(
            Question(
                dimension=dim,
                agree_pole=pole,
                text=text,
                is_active=bool(row.get("is_active", True)),
                source=str(row.get("source", "ai"))[:20],
            )
        )
        inserted += 1

    db.commit()
    return inserted

