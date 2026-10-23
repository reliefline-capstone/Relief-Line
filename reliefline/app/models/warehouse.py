# Database tables: warehouse stock and stock history.

from app.extensions import db

# Database table 'warehouse_inventory': stock on hand in each warehouse
# (food packs, kits, other items), with the minimum level that triggers a 'Low' warning.
class WarehouseInventory(db.Model):
    __tablename__ = "warehouse_inventory"

    inventory_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False, default="Food Packs")
    unit = db.Column(db.String(20), nullable=False, default="packs")
    quantity_available = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=0)
    expiration_date = db.Column(db.Date, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    office = db.relationship("Office", backref="inventory_items")


# Database table 'warehouse_stock_logs': the history of stock coming in and going out of a warehouse
# (restocks, donations, transfers, expired and damaged stock).
class WarehouseStockLog(db.Model):
    __tablename__ = "warehouse_stock_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    source_type = db.Column(db.Enum("standard", "donation", "dswd", "municipal", "returned_damaged", "expired"),
                             nullable=False, default="standard", server_default="standard")
    donor_name = db.Column(db.String(150), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    office = db.relationship("Office", backref="stock_logs")
    updated_by_user = db.relationship("User", foreign_keys=[updated_by])

    # True if this stock came from a donation.
    @property
    def is_donation(self):
        return self.source_type == "donation"

    # Where the stock came from, as shown on screen: Donation, DSWD Supply, or City/Municipal Supply.
    @property
    def source_label(self):
        return {"donation": "Donation", "dswd": "DSWD Supply", "municipal": "City/Municipal Supply"}.get(self.source_type)

    # True if this was damaged stock returned to the warehouse.
    @property
    def is_damaged_return(self):
        return self.source_type == "returned_damaged"

    # True if this movement is for expired stock.
    @property
    def is_expired(self):
        return self.source_type == "expired"
