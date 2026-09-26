"""
Creates/upgrades the tables and columns the SARIMAX forecaster needs. There is
no migration tool in this project (the committed reliefline_db.sql IS the
schema), so this is the hand-written, idempotent equivalent: safe to run any
number of times. After running it, sync the dump:

    .venv/Scripts/python.exe scripts/apply_timeseries_schema.py
    bash scripts/sync_db_dump.sh

Adds:
  * barangay_monthly_history  - barangay x month food packs (the time series)
  * climate_monthly           - monthly rainfall normal / ONI / storm context
  * barangays.flood_susceptibility, river_proximity_km, elevation_m,
    hazard_source
  * model_metrics.wape, p90_coverage, naive_wape
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    """
    CREATE TABLE IF NOT EXISTS barangay_monthly_history (
        history_id INT NOT NULL AUTO_INCREMENT,
        barangay_id INT NOT NULL,
        month_start DATE NOT NULL,
        food_packs INT NOT NULL DEFAULT 0,
        affected_families INT NOT NULL DEFAULT 0,
        event_count SMALLINT NOT NULL DEFAULT 0,
        max_event_severity SMALLINT NOT NULL DEFAULT 0,
        data_source VARCHAR(20) NOT NULL DEFAULT 'synthetic',
        PRIMARY KEY (history_id),
        UNIQUE KEY uq_history_barangay_month (barangay_id, month_start),
        KEY ix_history_month (month_start),
        CONSTRAINT fk_history_barangay FOREIGN KEY (barangay_id)
            REFERENCES barangays (barangay_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS climate_monthly (
        month_start DATE NOT NULL,
        rainfall_normal_mm DECIMAL(7,1) NOT NULL,
        rainfall_mm DECIMAL(7,1) NOT NULL,
        oni DECIMAL(3,1) DEFAULT NULL,
        event_count SMALLINT NOT NULL DEFAULT 0,
        max_event_severity SMALLINT NOT NULL DEFAULT 0,
        data_source VARCHAR(40) NOT NULL DEFAULT 'rain:synthetic;oni:noaa',
        PRIMARY KEY (month_start)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "ALTER TABLE barangays ADD COLUMN IF NOT EXISTS flood_susceptibility SMALLINT DEFAULT 2",
    "ALTER TABLE barangays ADD COLUMN IF NOT EXISTS river_proximity_km DECIMAL(5,2) DEFAULT NULL",
    "ALTER TABLE barangays ADD COLUMN IF NOT EXISTS elevation_m DECIMAL(6,1) DEFAULT NULL",
    "ALTER TABLE barangays ADD COLUMN IF NOT EXISTS hazard_source VARCHAR(20) DEFAULT 'synthetic'",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS wape DECIMAL(10,4) DEFAULT NULL",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS p90_coverage DECIMAL(6,4) DEFAULT NULL",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS naive_wape DECIMAL(10,4) DEFAULT NULL",
    # Error of the 12-month TOTAL (the stock-planning number) and the same
    # figure for the seasonal-naive benchmark.
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS total12_err DECIMAL(10,4) DEFAULT NULL",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS naive_total12_err DECIMAL(10,4) DEFAULT NULL",
]


def ensure_schema():
    for stmt in DDL:
        db.session.execute(text(stmt))
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        ensure_schema()
        for table in ("barangay_monthly_history", "climate_monthly"):
            n = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"{table}: {n} rows")
        print("Schema OK.")
