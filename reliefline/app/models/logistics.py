# Database table: stock transfers between warehouses.

from app.extensions import db

# Database table 'warehouse_transfers': stock moved between warehouses
# (PSWDO depot to a municipal warehouse, or depot to depot), with its delivery progress and receipt check.
class WarehouseTransfer(db.Model):
    __tablename__ = "warehouse_transfers"

    transfer_id = db.Column(db.Integer, primary_key=True)
    from_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    to_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.Enum("food_pack", "hygiene_kit", "kitchen_kit"), default="food_pack")
    quantity = db.Column(db.Integer, nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("relief_request_batches.batch_id"), nullable=True)
    status = db.Column(db.Enum("pending", "completed", "cancelled"), default="pending")
    dispatch_status = db.Column(db.Enum("preparing", "in_transit", "delivered"), nullable=True)
    expected_arrival = db.Column(db.Date, nullable=True)
    issued_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    received_by = db.Column(db.String(150), nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
    batch_lots = db.Column(db.Text, nullable=True)
    note = db.Column(db.String(255), nullable=True)
    receipt_condition = db.Column(db.String(20), nullable=True)
    quantity_received = db.Column(db.Integer, nullable=True)
    quantity_damaged = db.Column(db.Integer, nullable=True)
    receipt_note = db.Column(db.String(255), nullable=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    requested_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    completed_at = db.Column(db.DateTime, nullable=True)

    from_office = db.relationship("Office", foreign_keys=[from_office_id])
    to_office = db.relationship("Office", foreign_keys=[to_office_id])
    requested_by_user = db.relationship("User", foreign_keys=[requested_by])
    issued_by_user = db.relationship("User", foreign_keys=[issued_by])
    batch = db.relationship("ReliefRequestBatch", backref="transfers")

    # How many packs the receiving office actually counted on arrival
    # (the full amount if they didn't report a different number).
    @property
    def received_count(self):
        return self.quantity if self.quantity_received is None else self.quantity_received

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
        return max((self.quantity or 0) - self.received_count, 0)

    # True if the receiving office reported the delivery as incomplete or damaged.
    @property
    def has_receipt_issue(self):
        return self.receipt_condition in ("partial", "damaged")

    # The transfer's reference number shown on screen, e.g. TR-2026-012.
    @property
    def ref(self):
        return f"TR-{self.requested_at.year if self.requested_at else 2026}-{self.transfer_id:03d}"
