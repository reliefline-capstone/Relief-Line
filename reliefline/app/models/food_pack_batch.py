# Database tables: food pack contents and batches (with expiration dates).

from app.extensions import db

# Database table 'food_pack_components': what goes inside one food pack (rice, canned goods, coffee...)
# and how many days each item normally lasts before it expires.
class FoodPackComponent(db.Model):
    __tablename__ = "food_pack_components"

    component_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    quantity_label = db.Column(db.String(50), nullable=False)
    shelf_life_days = db.Column(db.Integer, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# Database table 'food_pack_batches': a group of food packs received by a warehouse on the same day.
# Its expiration date is the date of its earliest-expiring item.
class FoodPackBatch(db.Model):
    __tablename__ = "food_pack_batches"

    batch_id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=False)
    quantity_remaining = db.Column(db.Integer, nullable=False)
    received_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("active", "expired"), nullable=False,
                        default="active", server_default="active")
    expired_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    office = db.relationship("Office", backref="food_pack_batches")


# Database table 'food_pack_batch_items': the items inside a warehouse food pack batch,
# each with its own expiration date.
class FoodPackBatchItem(db.Model):
    __tablename__ = "food_pack_batch_items"

    item_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("food_pack_batches.batch_id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("food_pack_components.component_id"), nullable=True)
    custom_name = db.Column(db.String(100), nullable=True)
    quantity_label = db.Column(db.String(50), nullable=True)
    expiration_date = db.Column(db.Date, nullable=False)

    batch = db.relationship("FoodPackBatch", backref=db.backref(
        "items", order_by="FoodPackBatchItem.expiration_date"
    ))
    component = db.relationship("FoodPackComponent")

    # The item's name (e.g. 'Rice'), or the custom name typed in for an 'Other' item.
    @property
    def label(self):
        return self.component.name if self.component else self.custom_name

    # How much of the item is in one pack (e.g. '3 pcs').
    @property
    def qty_label(self):
        return self.quantity_label or (self.component.quantity_label if self.component else "")


# Database table 'barangay_food_pack_batches': a group of food packs a barangay received together,
# with its expiration date.
class BarangayFoodPackBatch(db.Model):
    __tablename__ = "barangay_food_pack_batches"

    batch_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    quantity_remaining = db.Column(db.Integer, nullable=False)
    received_date = db.Column(db.Date, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("active", "expired"), nullable=False,
                        default="active", server_default="active")
    expired_at = db.Column(db.DateTime, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    barangay = db.relationship("Barangay", backref="food_pack_batches")


# Database table 'barangay_food_pack_batch_items': the items inside a barangay food pack batch,
# each with its own expiration date.
class BarangayFoodPackBatchItem(db.Model):
    __tablename__ = "barangay_food_pack_batch_items"

    item_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("barangay_food_pack_batches.batch_id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("food_pack_components.component_id"), nullable=True)
    custom_name = db.Column(db.String(100), nullable=True)
    quantity_label = db.Column(db.String(50), nullable=True)
    expiration_date = db.Column(db.Date, nullable=False)

    batch = db.relationship("BarangayFoodPackBatch", backref=db.backref(
        "items", order_by="BarangayFoodPackBatchItem.expiration_date"
    ))
    component = db.relationship("FoodPackComponent")

    # The item's name (e.g. 'Rice'), or the custom name typed in for an 'Other' item.
    @property
    def label(self):
        return self.component.name if self.component else self.custom_name

    # How much of the item is in one pack (e.g. '3 pcs').
    @property
    def qty_label(self):
        return self.quantity_label or (self.component.quantity_label if self.component else "")
