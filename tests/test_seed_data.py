from __future__ import annotations

import json


def test_seed_has_enough_questions():
    data = json.loads(open("app/data/seed_questions.json", "r", encoding="utf-8").read())
    dims = {"EI": 0, "SN": 0, "TF": 0, "JP": 0}
    for q in data:
        dims[q["dimension"]] += 1
    assert all(v >= 25 for v in dims.values())

