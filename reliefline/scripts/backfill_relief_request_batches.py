"""
One-time backfill: wraps every existing "orphan" AllocationRecord (batch_id
IS NULL — created directly by an earlier version of scripts/seed_demo_data.py
rather than through the real CSWDO "Relief Requests" submission flow) in a
synthetic ReliefRequestBatch, grouped by (office, event).

Without this, orphaned AllocationRecords are invisible on the CSWDO Relief
Requests page (which only reads ReliefRequestBatch) while still showing up on
the CSWDO Dashboard's "Relief Request Status" widget (which reads
AllocationRecord directly) — the two pages silently disagree about how many
requests exist for the same underlying data. seed_demo_data.py no longer
creates orphans going forward; this script only needs to run once against a
database that was seeded before that fix.

Safe to re-run: only touches AllocationRecords that still have batch_id IS NULL.

Usage:
    .venv/Scripts/python.exe scripts/backfill_relief_request_batches.py
"""
import sys
import os
from datetime import datetime, time as dtime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.allocation import AllocationRecord
from app.models.relief_request_batch import ReliefRequestBatch
from app.models.user import User

app = create_app()

with app.app_context():
    orphans = AllocationRecord.query.filter(AllocationRecord.batch_id.is_(None)).all()
    if not orphans:
        print("No orphan AllocationRecords found — nothing to backfill.")
        sys.exit(0)

    cswdo_admin_by_office = {u.office_id: u for u in User.query.filter_by(role="cswdo_admin").all()}

    groups = {}
    for a in orphans:
        groups.setdefault((a.office_id, a.event_id), []).append(a)

    for (office_id, event_id), records in groups.items():
        total = sum(r.predicted_quantity or 0 for r in records)
        submitted_at = datetime.combine(min(r.allocation_date for r in records), dtime(9, 0))
        cswdo_admin = cswdo_admin_by_office.get(office_id)

        batch = ReliefRequestBatch(
            office_id=office_id, event_id=event_id,
            requested_food_packs=total, priority="medium",
            reason="Verified barangay reports show typhoon-related flooding requiring food pack support.",
            created_by=cswdo_admin.user_id if cswdo_admin else None,
            created_at=submitted_at, submitted_at=submitted_at,
        )
        db.session.add(batch)
        db.session.flush()

        for r in records:
            r.batch_id = batch.batch_id

        print(f"{batch.ref}: office_id={office_id} event_id={event_id} -> "
              f"{len(records)} records, {total:,} packs")

    db.session.commit()
    print(f"\nBackfilled {len(orphans)} AllocationRecords into {len(groups)} ReliefRequestBatch rows.")
