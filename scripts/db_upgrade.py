from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import init_db


def main() -> None:
    init_db()
    print("Database schema is up to date.")


if __name__ == "__main__":
    main()
