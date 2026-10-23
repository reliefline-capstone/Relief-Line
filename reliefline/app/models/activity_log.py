# Database tables: activity log / notifications, daily operations numbers.

from app.extensions import db
from app.utils.timezone import ph_now

# Database table 'activity_logs': every recorded action (who did what, and when).
# It doubles as the notifications list - each row can be read or unread.
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocation_records.allocation_id"), nullable=True)
    distribution_id = db.Column(db.Integer, db.ForeignKey("distribution_records.distribution_id"), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("relief_request_batches.batch_id"), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=ph_now)

    actor = db.relationship("User", foreign_keys=[actor_id])
    office = db.relationship("Office")
    barangay = db.relationship("Barangay")
    allocation = db.relationship("AllocationRecord")
    distribution = db.relationship("DistributionRecord")
    batch = db.relationship("ReliefRequestBatch")


# Database table 'daily_ops_stats': daily operations numbers per office
# (e.g. how many delivery vehicles were active that day).
class DailyOpsStat(db.Model):
    __tablename__ = "daily_ops_stats"

    stat_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    stat_date = db.Column(db.Date, nullable=False)
    vehicles_active = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
