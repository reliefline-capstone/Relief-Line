# Database table: barangays covered by a local disaster event.

from app.extensions import db

# Database table 'event_barangays': which barangays a local disaster event covers
# (when a municipality declares an event for only some of its barangays).
class EventBarangay(db.Model):
    __tablename__ = "event_barangays"

    event_barangay_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("event_id", "barangay_id", name="uq_event_barangay"),)
