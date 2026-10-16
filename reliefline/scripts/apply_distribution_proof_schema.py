"""
Adds proof_photos (comma-separated filenames) to barangay_stock_logs - the
optional photo proof a barangay can attach when recording a distribution
(Inventory > Record Distribution, or a report's per-family Mark Received).
Files live in static/uploads/barangay_distributions/<log_id>/. Idempotent.
After running it, sync the dump:

    .venv/Scripts/python.exe scripts/apply_distribution_proof_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE barangay_stock_logs ADD COLUMN IF NOT EXISTS proof_photos VARCHAR(500) DEFAULT NULL AFTER family_id",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
