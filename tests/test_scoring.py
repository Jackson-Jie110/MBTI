from __future__ import annotations


def test_scoring_direction_and_percent():
    from app.services.scoring import score_dimension

    questions = [
        {"id": 1, "dimension": "EI", "agree_pole": "E"},
        {"id": 2, "dimension": "EI", "agree_pole": "E"},
    ]
    answers = {1: 5, 2: 1}  # +2 and -2 => score 0 => 50/50
    out = score_dimension("EI", questions, answers)
    assert out["first_pole"] == "E"
    assert out["second_pole"] == "I"
    assert out["first_percent"] == 50
    assert out["second_percent"] == 50


def test_score_all_builds_type():
    from app.services.scoring import score_all

    questions = [
        {"id": 1, "dimension": "EI", "agree_pole": "I"},
        {"id": 2, "dimension": "SN", "agree_pole": "N"},
        {"id": 3, "dimension": "TF", "agree_pole": "T"},
        {"id": 4, "dimension": "JP", "agree_pole": "J"},
    ]
    answers = {1: 5, 2: 5, 3: 5, 4: 5}
    out = score_all(questions, answers)
    assert out["type"] == "INTJ"


def test_is_near_boundary_gap_rule():
    from app.services.scoring import is_near_boundary

    assert is_near_boundary(52, threshold_gap_percent=10) is True
    assert is_near_boundary(55, threshold_gap_percent=10) is False
    assert is_near_boundary(50, threshold_gap_percent=10) is True

