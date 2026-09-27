from app.extensions import db

class WarehouseTransfer(db.Model):
    """Stock moving between warehouses.

    Two flavours:
      * PSWDO depot -> PSWDO depot: an instant redistribution (status jumps
        straight to 'completed', no batch_id, no dispatch tracking).
      * PSWDO depot -> CSWDO municipal warehouse: fulfilment of a Stock Request
        (batch_id set). PSWDO monitors this leg - preparing -> in_transit ->
        delivered - and the CSWDO warehouse only credits the stock when it
        confirms receipt (status -> 'completed', batch -> 'fulfilled').
    """
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
    # JSON breakdown of which Food Pack batches (and their per-item expiration
    # dates) were deducted from the source depot at dispatch - see
    # app.routes.pswdo._deduct_food_pack_batches. The receiving office reads it
    # back so the stock arrives with its real remaining shelf life.
    batch_lots = db.Column(db.Text, nullable=True)
    note = db.Column(db.String(255), nullable=True)
    # Receiving office's verification (see cswdo.receive_transfer): "complete",
    # "partial" (fewer packs than dispatched) or "damaged" (some arrived
    # damaged). NULL on transfers confirmed before this existed - treated as
    # complete. Only the undamaged packs are credited to the warehouse.
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

    @property
    def received_count(self):
        return self.quantity if self.quantity_received is None else self.quantity_received

    @property
    def damaged_count(self):
        return self.quantity_damaged or 0

    @property
    def good_count(self):
        return max(self.received_count - self.damaged_count, 0)

    @property
    def shortage_count(self):
        return max((self.quantity or 0) - self.received_count, 0)

    @property
    def has_receipt_issue(self):
        return self.receipt_condition in ("partial", "damaged")

    @property
    def ref(self):
        return f"TR-{self.requested_at.year if self.requested_at else 2026}-{self.transfer_id:03d}"
