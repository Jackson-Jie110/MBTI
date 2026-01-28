from __future__ import annotations


def test_balanced_selection_counts():
    from app.services.selection import select_balanced

    questions = []
    for dim in ["EI", "SN", "TF", "JP"]:
        for i in range(30):
            questions.append({"id": f"{dim}-{i}", "dimension": dim})

    picked = select_balanced(questions, total=20, rng_seed=1)
    assert len(picked) == 20

    counts = {d: 0 for d in ["EI", "SN", "TF", "JP"]}
    for q in picked:
        counts[q["dimension"]] += 1

    assert counts == {"EI": 5, "SN": 5, "TF": 5, "JP": 5}


def test_balanced_selection_rejects_invalid_total():
    from app.services.selection import select_balanced

    questions = [{"id": 1, "dimension": "EI"}]
    try:
        select_balanced(questions, total=10, rng_seed=1)
    except ValueError as e:
        assert "total" in str(e).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_balanced_selection_requires_enough_per_dimension():
    from app.services.selection import select_balanced

    questions = [{"id": i, "dimension": "EI"} for i in range(10)]
    try:
        select_balanced(questions, total=20, rng_seed=1)
    except ValueError as e:
        assert "SN" in str(e) or "TF" in str(e) or "JP" in str(e)
    else:
        raise AssertionError("Expected ValueError")

