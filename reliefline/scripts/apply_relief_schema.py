"""
Creates/upgrades the tables the real-data two-stage forecaster needs, and
retires nothing yet (see scripts/drop_synthetic_history.py for that, run only
after the new pipeline is verified). Idempotent, like apply_timeseries_schema.py:

    .venv/Scripts/python.exe scripts/apply_relief_schema.py
    bash scripts/sync_db_dump.sh

Adds:
  * typhoon_calendar          - the 36-event verified Pangasinan calendar
                                 (2021-2026), superseding app.ml.climate_reference.EVENTS
  * relief_events             - one row per transcribed real relief report
                                 (may span several calendar typhoons, e.g. a
                                 combined "Nika + Ofel + Pepito" report)
  * relief_event_typhoons     - many-to-many: relief_events <-> typhoon_calendar
  * barangay_relief_records   - one row per barangay per relief_event (the
                                 Stage 1/Stage 2 training data)
  * disaster_events.is_reference - marks the 36 calendar-seeded rows so they
                                 don't pollute the staff's live event pickers
                                 (see the 4 patched DisasterEvent.query call
                                 sites in app/routes/{cswdo,reports,barangay,pswdo}.py)
  * model_metrics.mae_baseline_equal_split / mae_baseline_avg_share - the two
                                 leave-one-typhoon-out baselines the new share
                                 model is validated against
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db

DDL = [
    """
    CREATE TABLE IF NOT EXISTS typhoon_calendar (
        typhoon_key VARCHAR(40) NOT NULL,
        typhoon_name VARCHAR(150) NOT NULL,
        classification VARCHAR(60) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE DEFAULT NULL,
        key_date DATE DEFAULT NULL,
        year SMALLINT NOT NULL,
        pangasinan_impact_confirmed VARCHAR(60) NOT NULL DEFAULT 'not confirmed',
        research_notes TEXT DEFAULT NULL,
        disaster_event_id INT DEFAULT NULL,
        PRIMARY KEY (typhoon_key),
        KEY ix_typhoon_calendar_start (start_date),
        CONSTRAINT fk_typhoon_calendar_event FOREIGN KEY (disaster_event_id)
            REFERENCES disaster_events (event_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS relief_events (
        relief_event_id INT NOT NULL AUTO_INCREMENT,
        city_municipality VARCHAR(100) NOT NULL,
        label VARCHAR(150) NOT NULL,
        report_date DATE DEFAULT NULL,
        source_file VARCHAR(120) DEFAULT NULL,
        is_raw_report_extraction TINYINT(1) NOT NULL DEFAULT 0,
        notes TEXT DEFAULT NULL,
        PRIMARY KEY (relief_event_id),
        KEY ix_relief_events_lgu (city_municipality)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS relief_event_typhoons (
        relief_event_id INT NOT NULL,
        typhoon_key VARCHAR(40) NOT NULL,
        PRIMARY KEY (relief_event_id, typhoon_key),
        CONSTRAINT fk_ret_event FOREIGN KEY (relief_event_id)
            REFERENCES relief_events (relief_event_id) ON DELETE CASCADE,
        CONSTRAINT fk_ret_typhoon FOREIGN KEY (typhoon_key)
            REFERENCES typhoon_calendar (typhoon_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS barangay_relief_records (
        record_id INT NOT NULL AUTO_INCREMENT,
        relief_event_id INT NOT NULL,
        barangay_id INT NOT NULL,
        affected_families INT DEFAULT NULL,
        affected_individuals INT DEFAULT NULL,
        food_packs_given INT DEFAULT NULL,
        total_families_snapshot INT DEFAULT NULL,
        total_individuals_snapshot INT DEFAULT NULL,
        PRIMARY KEY (record_id),
        UNIQUE KEY uq_relief_barangay (relief_event_id, barangay_id),
        CONSTRAINT fk_brr_event FOREIGN KEY (relief_event_id)
            REFERENCES relief_events (relief_event_id) ON DELETE CASCADE,
        CONSTRAINT fk_brr_barangay FOREIGN KEY (barangay_id)
            REFERENCES barangays (barangay_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "ALTER TABLE disaster_events ADD COLUMN IF NOT EXISTS is_reference TINYINT(1) NOT NULL DEFAULT 0",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS mae_baseline_equal_split DECIMAL(10,4) DEFAULT NULL",
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS mae_baseline_avg_share DECIMAL(10,4) DEFAULT NULL",
    # Packs-unit LOTO-CV of the FULL pipeline (share x that fold's severity.expected),
    # not just the share model alone - rmse/mape/r_squared already existed (SARIMAX-era,
    # unused by v9 until now) and are reused here; mae_packs is new since `mae` is
    # already the share-model's own MAE (a proportion, not packs).
    "ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS mae_packs DECIMAL(10,4) DEFAULT NULL",
]


def ensure_schema():
    for stmt in DDL:
        db.session.execute(text(stmt))
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        ensure_schema()
        for table in ("typhoon_calendar", "relief_events", "relief_event_typhoons", "barangay_relief_records"):
            n = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"{table}: {n} rows")
        print("Schema OK.")
