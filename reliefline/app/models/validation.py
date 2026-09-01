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

    # Set when CSWDO/MSWDO dispatches a follow-up delivery to cover packs that
    # arrived short or damaged on an earlier, already-validated delivery. Points
    # at that earlier DistributionRecord. Same allocation_id — a replacement is
    # not a new allocation decision, just making the barangay whole.
    replacement_of_id = db.Column(
        db.Integer, db.ForeignKey("distribution_records.distribution_id"), nullable=True
    )

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

    # Barangay-stated receipt breakdown, captured on Confirm Receipt:
    #   * quantity_received — how many food packs physically arrived (==
    #     quantity_released when condition="complete", a smaller number when
    #     "partial", good+damaged when "damaged").
    #   * quantity_damaged  — of those, how many arrived damaged (0 unless
    #     condition="damaged").
    # Usable stock added to the barangay's inventory is
    # (quantity_received - quantity_damaged). NULL on legacy rows.
    quantity_received = db.Column(db.Integer, nullable=True)
    quantity_damaged = db.Column(db.Integer, nullable=True)

    barangay = db.relationship("Barangay", backref="distribution_records")
    allocation = db.relationship("AllocationRecord", backref="distribution_records")
    issued_by_user = db.relationship("User", foreign_keys=[issued_by])
    replaces = db.relationship(
        "DistributionRecord", remote_side=[distribution_id], backref="replacements"
    )

    @property
    def is_issued(self):
        return self.issued_at is not None

    @property
    def is_validated(self):
        """Barangay confirmed receipt with a validation record."""
        return self.status == "confirmed"

    @property
    def received_count(self):
        """Food packs the barangay acknowledged receiving — falls back to the
        released quantity for legacy rows confirmed before the breakdown
        existed."""
        if self.quantity_received is not None:
            return self.quantity_received
        return self.quantity_released or 0

    @property
    def damaged_count(self):
        return self.quantity_damaged or 0

    @property
    def good_count(self):
        """Undamaged packs actually received — what lands in barangay stock."""
        return max(self.received_count - self.damaged_count, 0)

    @property
    def shortage_count(self):
        """How many fewer packs arrived than were released (0 if all/most made it)."""
        return max((self.quantity_released or 0) - self.received_count, 0)

    @property
    def missing_or_damaged(self):
        """Packs the barangay is still owed after this delivery — short packs
        plus damaged ones. Only meaningful once validated."""
        if not self.is_validated:
            return 0
        return self.shortage_count + self.damaged_count

    @property
    def replacement_sent(self):
        """Total packs already dispatched on replacement deliveries for this
        record (pending or not — they're on the way)."""
        return sum(r.quantity_released or 0 for r in self.replacements)

    @property
    def outstanding_deficit(self):
        """Packs still owed to the barangay for this delivery after accounting
        for any replacement already sent. Drives the 'Send Replacement' action."""
        return max(self.missing_or_damaged - self.replacement_sent, 0)