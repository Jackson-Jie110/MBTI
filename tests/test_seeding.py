from __future__ import annotations


def test_seed_questions_inserts_when_empty(db):
    from app.models import Question
    from app.seeding import seed_questions_if_empty

    assert db.query(Question).count() == 0
    inserted = seed_questions_if_empty(db)
    assert inserted > 0
    assert db.query(Question).count() == inserted


def test_seed_questions_noop_when_not_empty(db):
    from app.models import Question
    from app.seeding import seed_questions_if_empty

    db.add(
        Question(
            dimension="EI",
            agree_pole="E",
            text="占位题",
            is_active=True,
            source="test",
        )
    )
    db.commit()

    inserted = seed_questions_if_empty(db)
    assert inserted == 0

