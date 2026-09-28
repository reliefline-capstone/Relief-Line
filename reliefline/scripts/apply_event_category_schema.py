"""
Widens disaster_events.weather_condition (shown as "Event Category") from
VARCHAR(50) to VARCHAR(255) - it now holds several comma-joined categories
(e.g. "Typhoon, Flood, Storm Surge"). Safe to re-run. After running it:

    .venv/Scripts/python.exe scripts/apply_event_category_schema.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "ALTER TABLE disaster_events MODIFY COLUMN weather_condition VARCHAR(255) DEFAULT NULL",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        print("Schema OK.")
