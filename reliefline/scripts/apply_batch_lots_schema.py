"""
Adds batch_lots (JSON text) to warehouse_transfers and distribution_records so
the Food Pack batches deducted at dispatch travel with the stock to the
receiving office/barangay. Idempotent. After running it, sync the dump:

    .venv/Scripts/python.exe scripts/apply_batch_lots_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE warehouse_transfers ADD COLUMN IF NOT EXISTS batch_lots TEXT DEFAULT NULL",
    "ALTER TABLE distribution_records ADD COLUMN IF NOT EXISTS batch_lots TEXT DEFAULT NULL",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
