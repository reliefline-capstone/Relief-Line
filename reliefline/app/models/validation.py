# Database table: food pack deliveries to barangays.

from app.extensions import db

# Database table 'distribution_records': food pack deliveries to barangays -
# delivery steps, who received them, condition on arrival (complete, partial, damaged), and replacements.
class DistributionRecord(db.Model):
    __tablename__ = "distribution_records"

    distribution_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocation_records.allocation_id"), nullable=False)
    quantity_released = db.Column(db.Integer, default=0)
    distribution_date = db.Column(db.Date, nullable=False)
    validation_type = db.Column(db.Enum("photo", "signature"), nullable=True)
    validation_file = db.Column(db.String(500), nullable=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    status = db.Column(db.Enum("pending", "confirmed"), default="pending")
    submitted_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    issued_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    issuance_note = db.Column(db.String(255), nullable=True)

    replacement_of_id = db.Column(
        db.Integer, db.ForeignKey("distribution_records.distribution_id"), nullable=True
    )

    batch_lots = db.Column(db.Text, nullable=True)

    dispatch_status = db.Column(
        db.Enum("preparing", "loaded", "dispatched", "in_transit", "delivered"),
        default="preparing"
    )
    departure_time = db.Column(db.Time, nullable=True)
    expected_arrival_time = db.Column(db.Time, nullable=True)

    received_by = db.Column(db.String(150), nullable=True)
    time_received = db.Column(db.Time, nullable=True)
    condition = db.Column(db.Enum("complete", "partial", "damaged"), nullable=True)
    travel_time = db.Column(db.String(50), nullable=True)

    quantity_received = db.Column(db.Integer, nullable=True)
    quantity_damaged = db.Column(db.Integer, nullable=True)

    barangay = db.relationship("Barangay", backref="distribution_records")
    allocation = db.relationship("AllocationRecord", backref="distribution_records")
    issued_by_user = db.relationship("User", foreign_keys=[issued_by])
    replaces = db.relationship(
        "DistributionRecord", remote_side=[distribution_id], backref="replacements"
    )

    # True if the delivery has been released from the warehouse.
    @property
    def is_issued(self):
        return self.issued_at is not None

    # True if the barangay confirmed it received the delivery.
    @property
    def is_validated(self):
        return self.status == "confirmed"

    # How many packs the barangay actually counted on arrival
    # (the full amount if they didn't report a different number).
    @property
    def received_count(self):
        if self.quantity_received is not None:
            return self.quantity_received
        return self.quantity_released or 0

    # How many of the received packs were damaged.
    @property
    def damaged_count(self):
        return self.quantity_damaged or 0

    # How many received packs are in good condition (received minus damaged).
    @property
    def good_count(self):
        return max(self.received_count - self.damaged_count, 0)

    # How many packs were missing on arrival (sent minus received).
    @property
    def shortage_count(self):
        return max((self.quantity_released or 0) - self.received_count, 0)

    # Total packs missing or damaged - counted only after the barangay confirms receipt.
    @property
    def missing_or_damaged(self):
        if not self.is_validated:
            return 0
        return self.shortage_count + self.damaged_count

    # How many replacement packs were already sent for this delivery.
    @property
    def replacement_sent(self):
        return sum(r.quantity_released or 0 for r in self.replacements)

    # Packs still owed to the barangay: missing/damaged packs minus replacements already sent.
    @property
    def outstanding_deficit(self):
        return max(self.missing_or_damaged - self.replacement_sent, 0)
