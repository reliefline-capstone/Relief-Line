"""
Adds safety_reserve_pct to offices - the % of an LGU's per-storm P90 that
its CSWDO/MSWDO keeps as a monthly safety reserve for months the forecaster
gives 0 (no typhoon on record). Default 10. Idempotent. After running it,
sync the dump:

    .venv/Scripts/python.exe scripts/apply_safety_reserve_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE offices ADD COLUMN IF NOT EXISTS safety_reserve_pct INT NOT NULL DEFAULT 10 AFTER capacity_food_pack",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
