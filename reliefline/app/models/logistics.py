from app.extensions import db

class WarehouseTransfer(db.Model):
    """Inter-warehouse redistribution request, per the PSWDO pre-positioning
    workflow (identify low-stock warehouses, redistribute from healthier ones)."""
    __tablename__ = "warehouse_transfers"

    transfer_id = db.Column(db.Integer, primary_key=True)
    from_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    to_office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.Enum("food_pack", "hygiene_kit", "kitchen_kit"), default="food_pack")
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("pending", "completed", "cancelled"), default="pending")
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    requested_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    completed_at = db.Column(db.DateTime, nullable=True)

    from_office = db.relationship("Office", foreign_keys=[from_office_id])
    to_office = db.relationship("Office", foreign_keys=[to_office_id])
    requested_by_user = db.relationship("User", foreign_keys=[requested_by])
