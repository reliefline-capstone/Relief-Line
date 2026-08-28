from app.extensions import db


class ReliefRequestBatch(db.Model):
    """A **Stock Request** — one CSWDO/MSWDO office asking PSWDO to replenish
    its municipal warehouse (Tier 2). This is the ONLY request PSWDO decides on:
    barangay-level Relief Requests (Tier 1) are handled entirely by CSWDO from
    its own warehouse and never reach PSWDO.

    On approval PSWDO performs a WarehouseTransfer from a provincial depot into
    the requesting CSWDO warehouse and monitors that leg (the manuscript's
    "PSWDO ... coordinates pre-positioning" + "from PSWDO to CSWDO lang ang
    monitoring"). The batch's own `status` column tracks the decision directly
    — no per-barangay fan-out.

    (Historically a batch spawned one AllocationRecord per barangay; those rows
    still exist and `allocation_records` still resolves them, but new batches
    don't create any.)
    """
    __tablename__ = "relief_request_batches"

    batch_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    # Auto-linked to PSWDO's active typhoon-related event when one exists;
    # standing (NULL) otherwise.
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)

    requested_food_packs = db.Column(db.Integer, default=0)
    priority = db.Column(db.Enum("high", "medium", "low"), default="medium")
    reason = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    # draft -> pending -> {approved | partially_approved | declined} -> fulfilled
    # (fulfilled = the replenishment transfer was received by the CSWDO warehouse)
    status = db.Column(
        db.Enum("draft", "pending", "approved", "partially_approved", "declined", "fulfilled"),
        nullable=False, default="draft", server_default="draft",
    )
    approved_food_packs = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    fulfilling_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    decided_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decision_remarks = db.Column(db.Text, nullable=True)

    # Comma-joined filenames, same convention as DistributionRecord.validation_file
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

    @property
    def is_draft(self):
        return self.status == "draft" or self.submitted_at is None

    @property
    def display_status(self):
        return "draft" if self.is_draft else self.status

    @property
    def ref(self):
        # "SR" = Stock Request (CSWDO -> PSWDO). Distinct from a barangay's
        # "RR" Relief Request (BarangayReport.ref).
        year = (self.submitted_at or self.created_at).year
        return f"SR-{year}-{self.batch_id:03d}"

    @property
    def transfer(self):
        """The WarehouseTransfer PSWDO created to fulfil this request, if any."""
        from app.models.logistics import WarehouseTransfer
        return WarehouseTransfer.query.filter_by(batch_id=self.batch_id).order_by(
            WarehouseTransfer.transfer_id.desc()
        ).first()

    @property
    def allocation_records(self):
        """Legacy per-barangay children — only pre-Phase-3 batches have these."""
        from app.models.allocation import AllocationRecord
        return AllocationRecord.query.filter_by(batch_id=self.batch_id).order_by(
            AllocationRecord.allocation_id
        ).all()
