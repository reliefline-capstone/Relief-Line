"""
One-time backfill: fills in the allocation_id/distribution_id/batch_id
columns (see app/models/activity_log.py) on ActivityLog rows created before
those columns existed, so old Notifications entries also get a specific
"View" destination instead of falling back to a non-clickable card.

Matches each row to its source record using the office_id/barangay_id
already stored on the log, narrowed by the action's implied status
(approved/rejected/delivered/etc.) and, when more than one candidate
remains, the record whose own date is closest to the log's created_at.
Safe for this dataset's small volume (a handful of demo rows) — going
forward, every new ActivityLog row is created with these columns already
populated directly (see app/routes/pswdo.py, app/routes/cswdo.py), so this
script only ever needs to run once against data that predates that fix.

Safe to re-run: only touches rows where the relevant column is still NULL.

Usage:
    .venv/Scripts/python.exe scripts/backfill_activity_log_references.py
"""
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.activity_log import ActivityLog
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.relief_request_batch import ReliefRequestBatch

app = create_app()


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    return value


def _closest(candidates, target_date, date_fn):
    dated = [(c, _as_date(date_fn(c))) for c in candidates]
    dated = [(c, d) for c, d in dated if d is not None]
    if not dated:
        return candidates[0] if candidates else None
    return min(dated, key=lambda pair: abs((pair[1] - target_date).days))[0]


def run():
    with app.app_context():
        updated = {"allocation": 0, "distribution": 0, "batch": 0}

        for log in ActivityLog.query.filter(
            ActivityLog.action_type.in_(["allocation_approved", "allocation_rejected"]),
            ActivityLog.allocation_id.is_(None),
        ).all():
            # office_id isn't a reliable filter here: the real approve route
            # stores the FULFILLING office, the real reject route stores the
            # REQUESTING office, and some older seed data used the fulfilling
            # office for both — barangay_id + the action's implied status is
            # the one thing that's consistent across all three sources.
            q = AllocationRecord.query.filter_by(barangay_id=log.barangay_id)
            q = q.filter(AllocationRecord.status == "approved") if log.action_type == "allocation_approved" \
                else q.filter(AllocationRecord.rejection_reason.isnot(None))
            candidates = q.all()
            match = _closest(candidates, _as_date(log.created_at), lambda a: a.allocation_date)
            if match:
                log.allocation_id = match.allocation_id
                updated["allocation"] += 1

        for log in ActivityLog.query.filter(
            ActivityLog.action_type.in_(["distribution_status", "distribution_delivered"]),
            ActivityLog.distribution_id.is_(None),
        ).all():
            q = DistributionRecord.query.filter_by(barangay_id=log.barangay_id)
            if log.office_id:
                q = q.join(AllocationRecord).filter(AllocationRecord.fulfilling_office_id == log.office_id)
            candidates = q.all()
            match = _closest(candidates, _as_date(log.created_at), lambda d: d.distribution_date)
            if match:
                log.distribution_id = match.distribution_id
                updated["distribution"] += 1

        for log in ActivityLog.query.filter(
            ActivityLog.action_type == "relief_request_submitted",
            ActivityLog.batch_id.is_(None),
        ).all():
            candidates = ReliefRequestBatch.query.filter_by(office_id=log.office_id).filter(
                ReliefRequestBatch.submitted_at.isnot(None)
            ).all()
            match = _closest(candidates, _as_date(log.created_at), lambda b: b.submitted_at)
            if match:
                log.batch_id = match.batch_id
                updated["batch"] += 1

        db.session.commit()
        print(f"Backfilled {updated['allocation']} allocation_id, "
              f"{updated['distribution']} distribution_id, "
              f"{updated['batch']} batch_id references.")


if __name__ == "__main__":
    run()
