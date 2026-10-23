# Database table: food pack allocations to barangays.

from app.extensions import db

# Database table 'allocation_records': food packs set aside for a barangay.
# It tracks how many were asked for, approved and released, which office supplies them, and the status.
class AllocationRecord(db.Model):
    __tablename__ = "allocation_records"

    allocation_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    predicted_quantity = db.Column(db.Integer, default=0)
    allocated_quantity = db.Column(db.Integer, default=0)
    historical_allocation = db.Column(db.Integer, default=0)
    allocation_date = db.Column(db.Date, nullable=False)
    disaster_event = db.Column(db.String(150), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)
    status = db.Column(db.Enum("pending", "approved", "released"), default="pending")
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    rejection_reason = db.Column(db.Text, nullable=True)
    fulfilling_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    decided_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    batch_id = db.Column(db.Integer, db.ForeignKey("relief_request_batches.batch_id"), nullable=True)

    source = db.Column(
        db.Enum("pswdo_batch", "barangay_request", "cswdo_direct"),
        nullable=False, default="pswdo_batch", server_default="pswdo_batch",
    )
    barangay_report_id = db.Column(
        db.Integer, db.ForeignKey("barangay_reports.report_id"), nullable=True
    )

    barangay = db.relationship("Barangay", backref="allocation_records")
    barangay_report = db.relationship("BarangayReport", foreign_keys=[barangay_report_id])
    office = db.relationship("Office", backref="allocation_records", foreign_keys=[office_id])
    fulfilling_office = db.relationship("Office", foreign_keys=[fulfilling_office_id])
    event = db.relationship("DisasterEvent", backref="allocation_records")
    submitted_by = db.relationship("User", foreign_keys=[created_by])
    decided_by_user = db.relationship("User", foreign_keys=[decided_by])

    # True if this allocation was rejected (a rejection reason was given).
    @property
    def is_rejected(self):
        return self.rejection_reason is not None

    # The status shown on screen.
    # It says 'partially approved' when fewer packs were approved than were asked for.
    @property
    def display_status(self):
        if self.is_rejected:
            return "rejected"
        if self.status == "approved" and self.allocated_quantity < self.predicted_quantity:
            return "partially_approved"
        return self.status
