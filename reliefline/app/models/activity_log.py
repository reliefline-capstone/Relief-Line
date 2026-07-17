from app.extensions import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DailyOpsStat(db.Model):
    __tablename__ = "daily_ops_stats"

    stat_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    stat_date = db.Column(db.Date, nullable=False)
    vehicles_active = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)