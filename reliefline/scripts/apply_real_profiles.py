"""
Writes the official figures in scripts/real_profiles.py onto the live
barangays table (population / num_households for Urdaneta City, PSA 2024).
seed_training_data.profile_for() already overlays them when it seeds, but a
database seeded before real_profiles.py existed keeps the old synthetic
numbers - run this to bring it up to date. Idempotent; only touches fields
that have a real value on record.

    .venv/Scripts/python.exe scripts/apply_real_profiles.py
    bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from scripts.real_profiles import real_profile


def apply_real_profiles():
    changed = 0
    for b in Barangay.query.all():
        real = real_profile(b.city_municipality, b.barangay_name)
        touched = False
        for field, value in real.items():
            if getattr(b, field) != value:
                setattr(b, field, value)
                touched = True
        changed += touched
    db.session.commit()
    return changed


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        n = apply_real_profiles()
        rows = db.session.execute(db.text(
            "SELECT city_municipality, COUNT(*), SUM(population), SUM(num_households) "
            "FROM barangays GROUP BY 1 ORDER BY 1")).fetchall()
        print(f"Updated {n} barangays from real_profiles.py")
        for r in rows:
            print(f"  {r[0]}: {r[1]} barangays, pop {int(r[2]):,}, households {int(r[3]):,}")
