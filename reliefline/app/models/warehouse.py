from app.extensions import db

class WarehouseInventory(db.Model):
    __tablename__ = "warehouse_inventory"

    inventory_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    # "food_pack" is a reserved key — the predictive/allocation pipeline and burn-rate
    # math key off it specifically. Any other slug (e.g. "rice_50kg") is a free-form
    # warehouse stock-monitoring line item with no predictive model behind it.
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False, default="Food Packs")
    unit = db.Column(db.String(20), nullable=False, default="packs")
    quantity_available = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    office = db.relationship("Office", backref="inventory_items")


class WarehouseStockLog(db.Model):
    """Manual stock adjustments (Add Stock / Update Stock) — feeds the 'Received'
    entries in the Stock Movement history, distinct from releases and transfers."""
    __tablename__ = "warehouse_stock_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    office = db.relationship("Office", backref="stock_logs")
    updated_by_user = db.relationship("User", foreign_keys=[updated_by])
