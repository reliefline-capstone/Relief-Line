# Database table: stock requests from CSWDO/MSWDO to PSWDO.

from app.extensions import db


# Database table 'relief_request_batches': stock requests a CSWDO/MSWDO sends to PSWDO
# (how many food packs, why, priority, attachments) and PSWDO's decision.
class ReliefRequestBatch(db.Model):
    __tablename__ = "relief_request_batches"

    batch_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)

    requested_food_packs = db.Column(db.Integer, default=0)
    priority = db.Column(db.Enum("high", "medium", "low"), default="medium")
    reason = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.Enum("draft", "pending", "approved", "partially_approved", "declined", "fulfilled"),
        nullable=False, default="draft", server_default="draft",
    )
    approved_food_packs = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    fulfilling_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    decided_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decision_remarks = db.Column(db.Text, nullable=True)

    damage_report_file = db.Column(db.String(255), nullable=True)
    photo_files = db.Column(db.String(500), nullable=True)
    other_files = db.Column(db.String(500), nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    submitted_at = db.Column(db.DateTime, nullable=True)

    office = db.relationship("Office", foreign_keys=[office_id])
    fulfilling_office = db.relationship("Office", foreign_keys=[fulfilling_office_id])
    event = db.relationship("DisasterEvent")
    created_by_user = db.relationship("User", foreign_keys=[created_by])
    decided_by_user = db.relationship("User", foreign_keys=[decided_by])

    # True if the request is still a draft (saved but not yet sent to PSWDO).
    @property
    def is_draft(self):
        return self.status == "draft" or self.submitted_at is None

    # The status shown on screen ('draft' until it is sent).
    @property
    def display_status(self):
        return "draft" if self.is_draft else self.status

    # True if the request should show a 'New' tag:
    # it is still waiting for a decision and its event hasn't ended.
    @property
    def is_new(self):
        if self.display_status != "pending":
            return False
        return not (self.event and self.event.status == "ended")

    # The request's reference number shown on screen, e.g. SR-2026-007.
    @property
    def ref(self):
        year = (self.submitted_at or self.created_at).year
        return f"SR-{year}-{self.batch_id:03d}"

    # The stock transfer that delivers this request, once PSWDO approves it.
    @property
    def transfer(self):
        from app.models.logistics import WarehouseTransfer
        return WarehouseTransfer.query.filter_by(batch_id=self.batch_id).order_by(
            WarehouseTransfer.transfer_id.desc()
        ).first()

    # The barangay allocations that were included in this request.
    @property
    def allocation_records(self):
        from app.models.allocation import AllocationRecord
        return AllocationRecord.query.filter_by(batch_id=self.batch_id).order_by(
            AllocationRecord.allocation_id
        ).all()
