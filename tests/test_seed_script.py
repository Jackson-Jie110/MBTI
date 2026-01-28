from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path


def test_seed_script_runs_and_inserts(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "scripts" / "seed_questions.py"

    db_path = tmp_path / "seed_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    completed = subprocess.run(
        [sys.executable, str(script_path), "--db", db_url],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("select count(*) from questions")
    count = cur.fetchone()[0]
    conn.close()

    assert count > 0
