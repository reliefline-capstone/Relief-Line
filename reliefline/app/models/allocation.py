from app.extensions import db

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

    # Decision fields — no new status enum values (rejection is tracked via
    # rejection_reason instead, since "pending" is otherwise unambiguous once set)
    rejection_reason = db.Column(db.Text, nullable=True)
    fulfilling_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    decided_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    barangay = db.relationship("Barangay", backref="allocation_records")
    office = db.relationship("Office", backref="allocation_records", foreign_keys=[office_id])
    fulfilling_office = db.relationship("Office", foreign_keys=[fulfilling_office_id])
    event = db.relationship("DisasterEvent", backref="allocation_records")
    submitted_by = db.relationship("User", foreign_keys=[created_by])
    decided_by_user = db.relationship("User", foreign_keys=[decided_by])

    @property
    def is_rejected(self):
        return self.rejection_reason is not None

    @property
    def display_status(self):
        if self.is_rejected:
            return "rejected"
        if self.status == "approved" and self.allocated_quantity < self.predicted_quantity:
            return "partially_approved"
        return self.status


class PrepositionRecord(db.Model):
    __tablename__ = "preposition_records"

    preposition_id = db.Column(db.Integer, primary_key=True)
    from_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    to_barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    item_type = db.Column(db.Enum("food_pack"), default="food_pack")
    quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum("pending", "approved", "completed"), default="pending")
    preposition_date = db.Column(db.Date, nullable=False)
    disaster_event = db.Column(db.String(150), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("disaster_events.event_id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    barangay = db.relationship("Barangay", backref="preposition_records")
    from_office = db.relationship("Office", backref="preposition_records")