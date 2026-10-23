# Database tables: barangay stock and stock history.

from app.extensions import db


# Database table 'barangay_inventory': how much stock (e.g. food packs) each barangay has on hand.
class BarangayInventory(db.Model):
    __tablename__ = "barangay_inventory"

    inventory_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False, default="Food Packs")
    unit = db.Column(db.String(20), nullable=False, default="packs")
    quantity_available = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"),
                             onupdate=db.func.now())
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    barangay = db.relationship("Barangay", backref="inventory_items")


# How many food packs a barangay has right now.
# Returns nothing if the barangay has no stock record yet.
def food_pack_on_hand(barangay_id):
    row = BarangayInventory.query.filter_by(
        barangay_id=barangay_id, item_type="food_pack"
    ).first()
    return row.quantity_available if row else None


# Database table 'barangay_stock_logs': the history of stock coming in and going out of a barangay
# (deliveries received, packs given to families, expired packs), with optional proof photos.
class BarangayStockLog(db.Model):
    __tablename__ = "barangay_stock_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    source_type = db.Column(
        db.Enum("delivery", "distribution", "adjustment", "damaged_return", "expired"),
        nullable=False, default="adjustment", server_default="adjustment",
    )
    distribution_id = db.Column(
        db.Integer, db.ForeignKey("distribution_records.distribution_id"), nullable=True
    )
    family_id = db.Column(
        db.Integer, db.ForeignKey("barangay_families.family_id", ondelete="SET NULL"), nullable=True
    )
    proof_photos = db.Column(db.String(500), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    barangay = db.relationship("Barangay", backref="stock_logs")

    # The list of proof photo file names attached to this stock movement.
    @property
    def proof_photo_list(self):
        return [n for n in (self.proof_photos or "").split(",") if n]
    updated_by_user = db.relationship("User", foreign_keys=[updated_by])
    family = db.relationship("Family")
