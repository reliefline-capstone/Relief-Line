"""
Adds warehouse_inventory.expiration_date - the optional expiration date for a
stock item added through "Add Stock Item" with "Does this item expire? = Yes".
(Food Packs keep their own per-component batch tracking; this is for every
other item.) Idempotent. There is no migration tool in this project, so after
running it, sync the dump:

    .venv/Scripts/python.exe scripts/apply_item_expiry_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE warehouse_inventory ADD COLUMN IF NOT EXISTS expiration_date DATE DEFAULT NULL",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
