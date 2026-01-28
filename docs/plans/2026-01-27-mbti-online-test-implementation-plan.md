# MBTI Online Test (FastAPI + SQLite) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Build a Chinese MBTI online test site with 20/40/60 modes, 5-point scale, SSR one-question-per-page, cross-device resume link+code, shareable result report, auto extra questions when a dimension is near the boundary.

**Architecture:** FastAPI serves SSR pages via Jinja2; SQLite stores question bank, test sessions, ordered test items, and answers. Core logic (question selection, scoring, reporting) lives in pure-Python services with unit tests.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, SQLAlchemy + SQLite, pytest.

---

### Task 1: Scaffold project layout & dependencies

**Files:**
- Create: `requirements.txt`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/templates/base.html`
- Create: `app/static/app.css`
- Create: `tests/test_smoke.py`

**Step 1: Write failing test**

`tests/test_smoke.py`
```python
def test_smoke_imports_app():
    from app.main import app  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL/ERROR because `app.main` missing

**Step 3: Write minimal implementation**

`app/main.py`
```python
from fastapi import FastAPI

app = FastAPI()
```

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

---

### Task 2: Add DB engine/session and models

**Files:**
- Create: `app/db.py`
- Create: `app/models.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test**

`tests/test_models.py`
```python
def test_models_create_tables(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        assert s.execute("SELECT 1").scalar() == 1
```

**Step 2: Run test (RED)**

Run: `pytest tests/test_models.py -q`
Expected: FAIL/ERROR (missing Base/models)

**Step 3: Minimal implementation**

- `app/models.py`: define `Base` and SQLAlchemy models:
  - `Question`
  - `Test`
  - `TestItem`
  - `Answer`
- Keep fields aligned with design document.

**Step 4: Run test (GREEN)**

Run: `pytest tests/test_models.py -q`
Expected: PASS

---

### Task 3: Implement token hashing, expiry helpers, and short-code generation

**Files:**
- Create: `app/services/tokens.py`
- Test: `tests/test_tokens.py`

**Step 1: Write failing test**

`tests/test_tokens.py`
```python
from datetime import timedelta

def test_hash_token_stable_with_secret():
    from app.services.tokens import hash_token
    assert hash_token("abc", secret="k") == hash_token("abc", secret="k")
    assert hash_token("abc", secret="k") != hash_token("abc", secret="k2")

def test_expiry_from_choice():
    from app.services.tokens import expiry_from_choice
    assert expiry_from_choice("1d") == timedelta(days=1)
    assert expiry_from_choice("7d") == timedelta(days=7)
    assert expiry_from_choice("30d") == timedelta(days=30)
    assert expiry_from_choice("permanent") is None
```

**Step 2: Run test (RED)**

Run: `pytest tests/test_tokens.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

`app/services/tokens.py`:
- `hash_token(token: str, secret: str) -> str` using `sha256(secret + token)`
- `new_url_token() -> str` (long token)
- `new_resume_code() -> str` (short code, e.g. 8 chars)
- `expiry_from_choice(choice: str) -> timedelta | None`

**Step 4: Run test (GREEN)**

Run: `pytest tests/test_tokens.py -q`
Expected: PASS

---

### Task 4: Implement balanced question selection & shuffle

**Files:**
- Create: `app/services/selection.py`
- Test: `tests/test_selection.py`

**Step 1: Write failing test**

`tests/test_selection.py`
```python
def test_balanced_selection_counts():
    from app.services.selection import select_balanced

    qs = [{"id": i, "dimension": d} for d in ["EI", "SN", "TF", "JP"] for i in range(100 * (["EI","SN","TF","JP"].index(d)+1), 100 * (["EI","SN","TF","JP"].index(d)+1) + 30)]
    picked = select_balanced(qs, total=20, rng_seed=1)
    assert len(picked) == 20
    counts = {d: 0 for d in ["EI", "SN", "TF", "JP"]}
    for q in picked:
        counts[q["dimension"]] += 1
    assert counts == {"EI": 5, "SN": 5, "TF": 5, "JP": 5}
```

**Step 2: Run test (RED)**

Run: `pytest tests/test_selection.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

`app/services/selection.py`:
- `select_balanced(questions, total, rng_seed=None)` returns list with `total/4` per dimension and then shuffled.
- Validate `total` is 20/40/60.
- Raise a clear exception if any dimension lacks enough questions.

**Step 4: Run test (GREEN)**

Run: `pytest tests/test_selection.py -q`
Expected: PASS

---

### Task 5: Implement scoring and “near boundary” detection

**Files:**
- Create: `app/services/scoring.py`
- Test: `tests/test_scoring.py`

**Step 1: Write failing test**

`tests/test_scoring.py`
```python
def test_scoring_direction_and_percent():
    from app.services.scoring import score_dimension

    # 2 questions, agree_pole is first pole (E)
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
```

**Step 2: Run test (RED)**

Run: `pytest tests/test_scoring.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

`app/services/scoring.py`:
- `score_dimension(dimension, questions, answers)` returns dict with score & percents
- `score_all(questions, answers)` returns 4-dimension result + type string
- `is_near_boundary(first_percent, threshold_gap_percent=10) -> bool`

**Step 4: Run test (GREEN)**

Run: `pytest tests/test_scoring.py -q`
Expected: PASS

---

### Task 6: Implement reporting (full analysis text)

**Files:**
- Create: `app/services/reporting.py`
- Create: `app/data/type_reports.json`
- Test: `tests/test_reporting.py`

**Step 1: Write failing test**

`tests/test_reporting.py`
```python
def test_report_has_required_sections():
    from app.services.reporting import build_report
    report = build_report("INTJ", {"EI": {"first_percent": 40, "second_percent": 60}}, boundary_notes=[])
    assert "优势" in report
    assert "盲点" in report
    assert "建议" in report
    assert "适合" in report
```

**Step 2: Run test (RED)**

Run: `pytest tests/test_reporting.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

- `app/data/type_reports.json`: provide 16 types’ Chinese sections.
- `build_report(type_code, dimensions, boundary_notes)` stitches type-level + dimension-level text.

**Step 4: Run test (GREEN)**

Run: `pytest tests/test_reporting.py -q`
Expected: PASS

---

### Task 7: Public routes & templates (start → test → finish → result)

**Files:**
- Create: `app/routes/public.py`
- Modify: `app/main.py`
- Create: `app/templates/home.html`
- Create: `app/templates/test.html`
- Create: `app/templates/finish.html`
- Create: `app/templates/result.html`
- Test: `tests/test_public_flow.py`

**Step 1: Write failing integration test**

`tests/test_public_flow.py`
```python
def test_start_to_first_question(client):
    r = client.get("/")
    assert r.status_code == 200
```

**Step 2: Run (RED)**

Run: `pytest tests/test_public_flow.py -q`
Expected: FAIL/ERROR (routes/templates missing)

**Step 3: Minimal implementation**

- Mount Jinja2 templates/static, implement `GET /` minimal page.
- Add `POST /start` creates test & sets cookie; redirect to `/test`.
- Add `GET /test` renders current question.
- Add `POST /answer` saves answer and navigates next/prev.
- Add `GET /finish` handles completion, extra-question loop, share expiry selection.
- Add `GET /result/{share_token}` read-only result page.
- Add `/resume` + `/resume/{resume_token}` endpoints.

**Step 4: Run (GREEN)**

Run: `pytest tests/test_public_flow.py -q`
Expected: PASS

---

### Task 8: Admin routes (localhost-only) for question management

**Files:**
- Create: `app/routes/admin.py`
- Create: `app/templates/admin_questions.html`
- Create: `app/templates/admin_edit_question.html`
- Test: `tests/test_admin_local_only.py`

**Step 1: Write failing test**

`tests/test_admin_local_only.py`
```python
def test_admin_denies_non_localhost(client, monkeypatch):
    r = client.get("/admin", headers={"x-forwarded-for": "8.8.8.8"})
    assert r.status_code in (403, 404)
```

**Step 2: Run (RED)**

Run: `pytest tests/test_admin_local_only.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

- Implement `/admin` list + create/edit + activate toggle.
- Implement import/export JSON.
- Enforce `request.client.host` is `127.0.0.1/::1`.

**Step 4: Run (GREEN)**

Run: `pytest tests/test_admin_local_only.py -q`
Expected: PASS

---

### Task 9: Seed initial AI question bank

**Files:**
- Create: `scripts/seed_questions.py`
- Create: `app/data/seed_questions.json`
- Test: `tests/test_seed_data.py`

**Step 1: Write failing test**

`tests/test_seed_data.py`
```python
import json

def test_seed_has_enough_questions():
    data = json.load(open("app/data/seed_questions.json", "r", encoding="utf-8"))
    dims = {"EI": 0, "SN": 0, "TF": 0, "JP": 0}
    for q in data:
        dims[q["dimension"]] += 1
    assert all(v >= 25 for v in dims.values())
```

**Step 2: Run (RED)**

Run: `pytest tests/test_seed_data.py -q`
Expected: FAIL/ERROR

**Step 3: Minimal implementation**

- Provide at least 25 active AI questions per dimension (Chinese).
- Seed script inserts them into SQLite.

**Step 4: Run (GREEN)**

Run: `pytest tests/test_seed_data.py -q`
Expected: PASS

---

### Task 10: End-to-end verification & docs

**Files:**
- Create: `README.md`

**Steps:**
- Run all tests: `pytest -q`
- Manual run: `uvicorn app.main:app --reload`
- Verify: start test, answer a few questions, resume via link/code, complete, see result page, admin list works on localhost.

---

## Notes

- This workspace is not a git repo; “commit” steps are optional unless `git init` is added later.

