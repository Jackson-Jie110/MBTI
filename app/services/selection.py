from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any


_DIMS = ("EI", "SN", "TF", "JP")


def _get_dimension(question: Any) -> str:
    if isinstance(question, dict):
        return str(question["dimension"])
    return str(getattr(question, "dimension"))


def select_balanced(questions: Sequence[Any], *, total: int, rng_seed: int | None = None) -> list[Any]:
    if total not in (20, 40, 60):
        raise ValueError(f"Invalid total={total!r}; expected one of 20/40/60")

    per_dim = total // 4
    buckets: dict[str, list[Any]] = {d: [] for d in _DIMS}
    for q in questions:
        dim = _get_dimension(q)
        if dim in buckets:
            buckets[dim].append(q)

    rng = random.Random(rng_seed)

    picked: list[Any] = []
    for dim in _DIMS:
        pool = buckets[dim]
        if len(pool) < per_dim:
            raise ValueError(f"Not enough questions for {dim}: need {per_dim}, have {len(pool)}")
        picked.extend(rng.sample(pool, per_dim))

    rng.shuffle(picked)
    return picked

