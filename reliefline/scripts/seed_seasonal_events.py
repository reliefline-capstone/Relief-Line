"""
Adds low-severity, OFF-SEASON synthetic disaster events (Jan/Feb/Mar/Apr/May/
Dec) on top of scripts/seed_training_data.py's six typhoon-season events
(Jun-Nov). Without this, four calendar months have zero AllocationRecord
history and the new time-forecasting model (app.ml.train) has nothing to
learn a seasonal shape from for a third of the year.

Severity multipliers here sit well below the typhoon-season band
(SYNTHETIC_EVENTS' 0.86-1.20) - these are minor, localized, non-typhoon
hazards (monsoon rains, flash floods, a heat advisory), consistent with real
Pangasinan/PAR climatology, where organized tropical cyclones are
overwhelmingly a June-December phenomenon (PAGASA). This deliberate
severity gap is what actually creates the seasonal CONTRAST the forecasting
model needs to see - six uniformly-severe typhoon events plus six much
smaller off-season ones, not twelve similar-sized events smeared evenly
across the year.

Reuses the exact same generative formula as seed_training_data.py
(synthetic_allocation, affected_families_for, status_tier) so the whole
synthetic dataset stays one coherent function - see that script's own
docstring for the formula itself.

Idempotent: skips any event whose name already exists. Run AFTER
scripts/seed_training_data.py (barangay profiles must already exist), and
re-run scripts/train_model.py afterward.

Usage:
    .venv/Scripts/python.exe scripts/seed_seasonal_events.py
"""
import os
import random
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ - sibling modules

from seed_training_data import affected_families_for, status_tier, synthetic_allocation

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.office import Office
from app.models.user import User
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.allocation import AllocationRecord
from app.ml.train import historical_allocation_for

app = create_app()

# (name, start, end, weather_condition, severity) - deliberately low
# severity, well below SYNTHETIC_EVENTS' 0.86-1.20 typhoon-season band.
OFF_SEASON_EVENTS = [
    ("Localized Flooding (Jan)",       date(2024, 1, 18), date(2024, 1, 20),  "Monsoon Rains", 0.35),
    ("Localized Flooding (Feb)",       date(2025, 2, 9),  date(2025, 2, 11),  "Monsoon Rains", 0.30),
    ("Summer Heat Advisory (Mar)",     date(2024, 3, 22), date(2024, 3, 23),  "Heat Wave",      0.20),
    ("Localized Flashflood (Apr)",     date(2025, 4, 14), date(2025, 4, 15),  "Flash Flood",    0.25),
    ("Pre-Monsoon Squall (May)",       date(2024, 5, 27), date(2024, 5, 28),  "Squall",         0.30),
    ("Amihan Tail-end Flooding (Dec)", date(2024, 12, 12), date(2024, 12, 14), "Monsoon Rains", 0.40),
]

# Lower than SYNTHETIC_EVENTS' 0.75 - these are localized/minor hazards, not
# province-wide typhoons, so a smaller share of barangays is realistically
# affected by any one of them.
HIT_RATE = 0.5


def run():
    with app.app_context():
        pswdo_admin = (User.query.filter_by(role="pswdo_admin").first()
                       or User.query.filter_by(role="system_admin").first())
        cswdo_office_by_lgu = {o.area_covered: o for o in Office.query.filter_by(office_type="cswdo").all()}
        all_barangays = Barangay.query.all()

        created_events = 0
        created_allocs = 0
        for ev_name, start, end, weather, severity in OFF_SEASON_EVENTS:
            if DisasterEvent.query.filter_by(event_name=ev_name).first() is not None:
                continue  # idempotent - already seeded

            event = DisasterEvent(
                event_name=ev_name, event_type="other", status="ended",
                weather_condition=weather, start_date=start, end_date=end,
                created_by=pswdo_admin.user_id if pswdo_admin else None,
            )
            db.session.add(event)
            db.session.flush()
            created_events += 1

            for b in all_barangays:
                hit_rng = random.Random(f"offseason_hit|{b.city_municipality}|{b.barangay_name}|{ev_name}")
                if hit_rng.random() >= HIT_RATE:
                    continue

                alloc_rng = random.Random(f"offseason_alloc|{b.city_municipality}|{b.barangay_name}|{ev_name}")
                prior = historical_allocation_for(b.barangay_id, before_date=start)
                qty = synthetic_allocation(b, severity, prior, alloc_rng)
                if qty <= 0:
                    continue
                affected_families = affected_families_for(b, severity, alloc_rng)

                office = cswdo_office_by_lgu.get(b.city_municipality)
                db.session.add(AllocationRecord(
                    barangay_id=b.barangay_id,
                    office_id=office.office_id if office else None,
                    predicted_quantity=qty,
                    allocated_quantity=qty,
                    historical_allocation=prior,
                    allocation_date=start,
                    event_id=event.event_id,
                    disaster_event=ev_name,
                    status="released",
                    created_by=pswdo_admin.user_id if pswdo_admin else None,
                    decided_by=pswdo_admin.user_id if pswdo_admin else None,
                ))
                created_allocs += 1

                if not BarangayDisasterStatus.query.filter_by(
                    barangay_id=b.barangay_id, event_id=event.event_id
                ).first():
                    db.session.add(BarangayDisasterStatus(
                        barangay_id=b.barangay_id, event_id=event.event_id,
                        status=status_tier(affected_families, b.num_households),
                        affected_families=affected_families,
                        updated_by=pswdo_admin.user_id if pswdo_admin else None,
                    ))
            db.session.flush()

        db.session.commit()
        print(f"Created {created_events} off-season event(s) and {created_allocs} released allocation(s).")
        print(f"Total AllocationRecords now: {AllocationRecord.query.count()}")
        print("\nNext: .venv/Scripts/python.exe scripts/train_model.py")


if __name__ == "__main__":
    run()
