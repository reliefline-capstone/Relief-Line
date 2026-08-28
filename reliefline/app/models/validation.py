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

    # Issuance confirmation record — the CSWDO/MSWDO side: "these packs were
    # released from our warehouse." Distinct from the validation record above
    # (status='confirmed' + validation_type/file), which is the barangay's
    # "we received them" with photo/signature. The manuscript keeps these two
    # confirmations separate on purpose. A barangay Relief Request only closes
    # (report -> 'fulfilled', barangay inventory bumped) on the barangay's
    # validation — never on issuance alone.
    issued_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    issuance_note = db.Column(db.String(255), nullable=True)

    # Dispatch/logistics lifecycle — tracks the trip itself, separate from proof-of-delivery above
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
    issued_by_user = db.relationship("User", foreign_keys=[issued_by])

    @property
    def is_issued(self):
        return self.issued_at is not None

    @property
    def is_validated(self):
        """Barangay confirmed receipt with a photo/signature validation record."""
        return self.status == "confirmed"