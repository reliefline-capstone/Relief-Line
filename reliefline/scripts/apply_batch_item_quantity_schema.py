"""
Adds quantity_label (what one pack holds of an item in a given batch, e.g.
"3 pcs") to both Food Pack batch-item tables. Idempotent. After running it:

    .venv/Scripts/python.exe scripts/apply_batch_item_quantity_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS quantity_label VARCHAR(50) DEFAULT NULL"
    for t in ("food_pack_batch_items", "barangay_food_pack_batch_items")
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
