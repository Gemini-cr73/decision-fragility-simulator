# tests/test_db.py

import sys
from pathlib import Path

# Ensure project root (decision-fragility-simulator) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.db import get_db_connection


def main():
    try:
        conn = get_db_connection()
        print("Connected OK:", conn.dsn)
        conn.close()
    except Exception as e:
        print("Database connection FAILED:", e)


if __name__ == "__main__":
    main()
