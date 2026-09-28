"""
Drops the synthetic-data tables/columns now that the two-stage forecaster
runs entirely on real relief data (app.ml.train, scripts/load_relief_events.py)
and scripts/check_forecast.py has passed. Irreversible against the live DB
(git history keeps the old schema/generator if this ever needs undoing).

Drops:
  * barangay_monthly_history, climate_monthly - the SARIMAX forecaster's
    ~97%-fabricated monthly training data (see app/ml/train.py module doc).
  * barangays.flood_susceptibility, river_proximity_km, elevation_m,
    hazard_source - only fed the old 60/40 history/vulnerability share blend
    (app.ml.predict.share_breakdown), dropped in favor of pure regression
    share per the confirmed design decision.

    .venv/Scripts/python.exe scripts/drop_synthetic_history.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    "DROP TABLE IF EXISTS barangay_monthly_history",
    "DROP TABLE IF EXISTS climate_monthly",
    "ALTER TABLE barangays DROP COLUMN IF EXISTS flood_susceptibility",
    "ALTER TABLE barangays DROP COLUMN IF EXISTS river_proximity_km",
    "ALTER TABLE barangays DROP COLUMN IF EXISTS elevation_m",
    "ALTER TABLE barangays DROP COLUMN IF EXISTS hazard_source",
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for stmt in DDL:
            db.session.execute(text(stmt))
        db.session.commit()
        remaining = db.session.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() "
            "AND table_name IN ('barangay_monthly_history', 'climate_monthly')")).scalar()
        print(f"Dropped. Synthetic tables remaining: {remaining}")
