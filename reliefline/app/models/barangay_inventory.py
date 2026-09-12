from app.extensions import db


class BarangayInventory(db.Model):
    """A barangay's own on-hand relief stock - a plain +/- ledger for
    operational visibility only (CSWDO/PSWDO can view it). It goes UP when a
    barangay confirms receipt of a CSWDO delivery and DOWN when barangay
    personnel record having handed goods out. It is deliberately NOT a model
    predictor - the manuscript fixes the six predictors (Objectives 1 & 2).
    """
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


def food_pack_on_hand(barangay_id):
    """This barangay's own current food-pack stock, or None when there is no
    inventory row on record at all.

    The distinction matters for the CSWDO/MSWDO-facing views (Barangay Report
    review, Predictive Analytics, GIS map): a real 0 means "we've handed
    everything out", while None means "the barangay has never reported any
    stock" - those must not read the same to someone deciding an allocation.
    """
    row = BarangayInventory.query.filter_by(
        barangay_id=barangay_id, item_type="food_pack"
    ).first()
    return row.quantity_available if row else None


class BarangayStockLog(db.Model):
    """Movement ledger behind BarangayInventory - one row per +/- change.

    source_type: 'delivery' (a confirmed CSWDO delivery, distribution_id set),
    'distribution' (barangay handed goods to residents), 'adjustment' (manual
    correction - recount, spoilage), 'damaged_return' (informational only,
    delta always 0 - damaged packs from a delivery never entered this
    barangay's usable stock in the first place, see app.routes.barangay.
    _return_damaged_packs; this row just records, for the barangay's own
    history, that they were sent back to the fulfilling office's warehouse).
    """
    __tablename__ = "barangay_stock_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    source_type = db.Column(
        db.Enum("delivery", "distribution", "adjustment", "damaged_return"),
        nullable=False, default="adjustment", server_default="adjustment",
    )
    distribution_id = db.Column(
        db.Integer, db.ForeignKey("distribution_records.distribution_id"), nullable=True
    )
    # Which registered Family this distribution went to, when the barangay
    # named one - set either from the per-report "Mark Received" checklist
    # (app.routes.barangay.mark_family_received) or from an optional family
    # picker on the generic "Record Distribution" form (inventory_record),
    # which works even for a family with no report at all. NULL means an
    # anonymous/bulk distribution, same as before this column existed.
    family_id = db.Column(
        db.Integer, db.ForeignKey("barangay_families.family_id", ondelete="SET NULL"), nullable=True
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    barangay = db.relationship("Barangay", backref="stock_logs")
    updated_by_user = db.relationship("User", foreign_keys=[updated_by])
    family = db.relationship("Family")
