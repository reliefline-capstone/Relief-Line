from app.extensions import db

class WarehouseInventory(db.Model):
    __tablename__ = "warehouse_inventory"

    inventory_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    item_type = db.Column(db.Enum("food_pack", "hygiene_kit", "kitchen_kit"), nullable=False)
    quantity_available = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=0)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    office = db.relationship("Office", backref="inventory_items")