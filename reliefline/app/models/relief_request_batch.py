from app.extensions import db

class ReliefRequestBatch(db.Model):
    """One CSWDO/MSWDO-initiated relief request to PSWDO, covering every
    barangay in the office's LGU that was verified (via Damage Assessment)
    for the batch's event but has no AllocationRecord yet.

    A batch itself carries no approve/reject decision — that stays exactly
    where it already lives, per-barangay, on AllocationRecord (approved by
    PSWDO via app.routes.pswdo.approve_relief_request/reject_relief_request).
    Submitting a batch creates one AllocationRecord per covered barangay,
    each tagged with this batch_id, so PSWDO's existing queue/approval flow
    needs no changes at all — a batch is purely a CSWDO-side grouping/
    submission wrapper around records PSWDO already knows how to process.

    submitted_at is NULL while the batch is still a draft (no
    AllocationRecords exist yet for it); it's set the moment "Submit to
    PSWDO" actually creates them.
    """
    __tablename__ = "relief_request_batches"

    batch_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=False)

    requested_food_packs = db.Column(db.Integer, default=0)
    priority = db.Column(db.Enum("high", "medium", "low"), default="medium")
    reason = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    # Comma-joined filenames, same convention as DistributionRecord.validation_file
    damage_report_file = db.Column(db.String(255), nullable=True)
    photo_files = db.Column(db.String(500), nullable=True)
    other_files = db.Column(db.String(500), nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    submitted_at = db.Column(db.DateTime, nullable=True)

    office = db.relationship("Office")
    event = db.relationship("DisasterEvent")
    created_by_user = db.relationship("User")

    @property
    def is_draft(self):
        return self.submitted_at is None

    @property
    def ref(self):
        year = (self.submitted_at or self.created_at).year
        return f"RR-{year}-{self.batch_id:03d}"

    @property
    def allocation_records(self):
        from app.models.allocation import AllocationRecord
        return AllocationRecord.query.filter_by(batch_id=self.batch_id).order_by(
            AllocationRecord.allocation_id
        ).all()

    @property
    def display_status(self):
        """draft | pending | approved | partially_approved | rejected — a
        roll-up over this batch's per-barangay AllocationRecords, since PSWDO
        decides each one independently."""
        if self.is_draft:
            return "draft"
        children = self.allocation_records
        if not children:
            return "pending"
        statuses = {c.display_status for c in children}
        if statuses == {"rejected"}:
            return "rejected"
        if statuses <= {"approved", "released"} and statuses:
            return "approved"
        if statuses == {"pending"}:
            return "pending"
        return "partially_approved"
