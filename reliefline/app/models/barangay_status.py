from app.extensions import db

class BarangayDisasterStatus(db.Model):
    __tablename__ = "barangay_disaster_status"

    status_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    status = db.Column(
        db.Enum("normal", "monitoring", "needs_assistance", "high_priority"),
        default="normal"
    )
    affected_families = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    barangay = db.relationship("Barangay", backref="disaster_statuses")