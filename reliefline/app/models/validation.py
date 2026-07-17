from app.extensions import db

class DistributionRecord(db.Model):
    __tablename__ = "distribution_records"

    distribution_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocation_records.allocation_id"), nullable=False)
    quantity_released = db.Column(db.Integer, default=0)
    distribution_date = db.Column(db.Date, nullable=False)
    # Proof-of-delivery fields — only meaningful once dispatch_status reaches "delivered".
    # validation_file may hold multiple comma-joined filenames (no separate attachments table yet).
    validation_type = db.Column(db.Enum("photo", "signature"), nullable=True)
    validation_file = db.Column(db.String(500), nullable=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    status = db.Column(db.Enum("pending", "confirmed"), default="pending")
    submitted_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    # Dispatch/logistics lifecycle — tracks the trip itself, separate from proof-of-delivery above
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.vehicle_id"), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.driver_id"), nullable=True)
    dispatch_status = db.Column(
        db.Enum("preparing", "loaded", "dispatched", "in_transit", "delivered", "delayed"),
        default="preparing"
    )
    departure_time = db.Column(db.Time, nullable=True)
    expected_arrival_time = db.Column(db.Time, nullable=True)

    # Delivery confirmation details — filled in when marking "delivered"
    received_by = db.Column(db.String(150), nullable=True)
    time_received = db.Column(db.Time, nullable=True)
    condition = db.Column(db.Enum("complete", "partial", "damaged"), nullable=True)
    travel_time = db.Column(db.String(50), nullable=True)

    barangay = db.relationship("Barangay", backref="distribution_records")
    allocation = db.relationship("AllocationRecord", backref="distribution_records")
    vehicle = db.relationship("Vehicle", backref="distribution_records")
    driver = db.relationship("Driver", backref="distribution_records")