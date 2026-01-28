from __future__ import annotations

from typing import Any


_DIMS = ("EI", "SN", "TF", "JP")
_POLES: dict[str, tuple[str, str]] = {
    "EI": ("E", "I"),
    "SN": ("S", "N"),
    "TF": ("T", "F"),
    "JP": ("J", "P"),
}


def _get(question: Any, key: str) -> Any:
    if isinstance(question, dict):
        return question[key]
    return getattr(question, key)


def dimension_poles(dimension: str) -> tuple[str, str]:
    try:
        return _POLES[dimension]
    except KeyError as e:
        raise ValueError(f"Unsupported dimension: {dimension!r}") from e


def is_near_boundary(first_percent: int, *, threshold_gap_percent: int = 10) -> bool:
    gap = abs(100 - 2 * int(first_percent))
    return gap < threshold_gap_percent


def score_dimension(
    dimension: str,
    questions: list[Any],
    answers: dict[Any, int],
) -> dict[str, Any]:
    first_pole, second_pole = dimension_poles(dimension)

    score = 0
    answered = 0
    for q in questions:
        if _get(q, "dimension") != dimension:
            continue
        qid = _get(q, "id")
        if qid not in answers:
            continue
        value = int(answers[qid])
        delta = value - 3
        agree_pole = str(_get(q, "agree_pole"))
        if agree_pole == first_pole:
            score += delta
        else:
            score -= delta
        answered += 1

    if answered <= 0:
        first_percent = 50
    else:
        max_abs = 2 * answered
        first_percent_f = (score / max_abs) * 50 + 50
        first_percent = int(round(first_percent_f))
        first_percent = max(0, min(100, first_percent))

    second_percent = 100 - first_percent
    gap_percent = abs(first_percent - second_percent)

    return {
        "dimension": dimension,
        "first_pole": first_pole,
        "second_pole": second_pole,
        "score": score,
        "answered": answered,
        "first_percent": first_percent,
        "second_percent": second_percent,
        "gap_percent": gap_percent,
    }


def score_all(questions: list[Any], answers: dict[Any, int]) -> dict[str, Any]:
    dimensions: dict[str, Any] = {}
    type_letters: list[str] = []
    for dim in _DIMS:
        out = score_dimension(dim, questions, answers)
        dimensions[dim] = out
        type_letters.append(out["first_pole"] if out["score"] >= 0 else out["second_pole"])

    return {"type": "".join(type_letters), "dimensions": dimensions}

