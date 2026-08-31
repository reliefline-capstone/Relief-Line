from app.extensions import db

class WarehouseTransfer(db.Model):
    """Stock moving between warehouses.

    Two flavours:
      * PSWDO depot -> PSWDO depot: an instant redistribution (status jumps
        straight to 'completed', no batch_id, no dispatch tracking).
      * PSWDO depot -> CSWDO municipal warehouse: fulfilment of a Stock Request
        (batch_id set). PSWDO monitors this leg — preparing -> in_transit ->
        delivered — and the CSWDO warehouse only credits the stock when it
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
    note = db.Column(db.String(255), nullable=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    requested_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    completed_at = db.Column(db.DateTime, nullable=True)

    from_office = db.relationship("Office", foreign_keys=[from_office_id])
    to_office = db.relationship("Office", foreign_keys=[to_office_id])
    requested_by_user = db.relationship("User", foreign_keys=[requested_by])
    issued_by_user = db.relationship("User", foreign_keys=[issued_by])
    batch = db.relationship("ReliefRequestBatch", backref="transfers")

    @property
    def ref(self):
        return f"TR-{self.requested_at.year if self.requested_at else 2026}-{self.transfer_id:03d}"
