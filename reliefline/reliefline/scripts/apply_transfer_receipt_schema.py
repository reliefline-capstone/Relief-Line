"""
Adds the receiving office's verification fields (complete / partial /
damaged) to warehouse_transfers. Idempotent. After running it:

    .venv/Scripts/python.exe scripts/apply_transfer_receipt_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE warehouse_transfers ADD COLUMN IF NOT EXISTS receipt_condition VARCHAR(20) DEFAULT NULL",
    "ALTER TABLE warehouse_transfers ADD COLUMN IF NOT EXISTS quantity_received INT DEFAULT NULL",
    "ALTER TABLE warehouse_transfers ADD COLUMN IF NOT EXISTS quantity_damaged INT DEFAULT NULL",
    "ALTER TABLE warehouse_transfers ADD COLUMN IF NOT EXISTS receipt_note VARCHAR(255) DEFAULT NULL",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
