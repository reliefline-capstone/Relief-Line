from app.extensions import db

class FoodPackComponent(db.Model):
    """Catalog of what one Food Pack physically contains, with a researched
    real-world shelf life per item (see scripts/seed_food_pack_batches.py for
    sourcing notes). This is what lets a batch's expiration be driven by
    whichever component spoils first - e.g. the rice, not the canned goods -
    instead of one made-up date for the whole pack.

    Seeded once by scripts/seed_food_pack_batches.py; no admin CRUD UI for it
    yet, so editing the contents/shelf lives today means updating that seed
    data and re-running it against a fresh row set.
    """
    __tablename__ = "food_pack_components"

    component_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    quantity_label = db.Column(db.String(50), nullable=False)
    shelf_life_days = db.Column(db.Integer, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class FoodPackBatch(db.Model):
    """One addition of Food Packs stock at a PSWDO/CSWDO warehouse, so shelf
    life can be tracked per-batch instead of as one running total.

    expiration_date is a cached copy of the earliest FoodPackBatchItem.expiration_date
    among this batch's components (see items relationship) - the whole batch
    of packs is pulled together once its most perishable component (in
    practice, the rice) expires, since a sealed relief pack isn't unbundled
    to salvage the canned goods inside. Set once at batch creation
    (_create_food_pack_batch in app.routes.pswdo) and not recomputed after,
    since components aren't edited post-receipt in this version.

    quantity_remaining is best-effort FIFO accounting, not a hard per-unit
    trace: outgoing movements (dispatches, transfers) adjust
    WarehouseInventory.quantity_available directly without touching a
    specific batch, so app.routes.pswdo._sync_food_pack_batches trims the
    oldest batches first whenever the batch total runs ahead of the real
    on-hand count. See that function for the expiry-transition logic.
    """
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


class FoodPackBatchItem(db.Model):
    """One component's actual expiration date within one FoodPackBatch - e.g.
    "the rice in batch #42 expires 2027-03-01". Generated automatically at
    batch creation from FoodPackComponent.shelf_life_days (received_date +
    shelf_life_days), not hand-entered - see _create_food_pack_batch."""
    __tablename__ = "food_pack_batch_items"

    item_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("food_pack_batches.batch_id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("food_pack_components.component_id"), nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)

    batch = db.relationship("FoodPackBatch", backref=db.backref(
        "items", order_by="FoodPackBatchItem.expiration_date"
    ))
    component = db.relationship("FoodPackComponent")
