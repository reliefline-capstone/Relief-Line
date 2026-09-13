from app.extensions import db

class EventBarangay(db.Model):
    """Explicit barangay membership for a scope="municipality" DisasterEvent -
    which of a CSWDO's own barangays their local declare actually covers.
    Unused for scope="province" events, which implicitly cover every
    barangay (same behavior as before this table existed)."""
    __tablename__ = "event_barangays"

    event_barangay_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("event_id", "barangay_id", name="uq_event_barangay"),)
