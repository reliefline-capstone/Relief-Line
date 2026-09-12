"""
Seeds the FoodPackComponent catalog (what one Food Pack physically contains,
with a researched real-world shelf life per item) and backfills FoodPackBatch
+ FoodPackBatchItem rows for each PSWDO/CSWDO office's current "food_pack"
stock, so the shelf-life / expiration monitoring feature has something
realistic to show immediately instead of an empty Food Pack Batches panel.

Pack contents and researched shelf life (see sources below; values picked at
the conservative/shorter end of each range, appropriate for relief goods
that aren't always stored under ideal retail conditions):

  Rice (Bigas), 1 sack        ~6 months  (180 days)
    Milled rice keeps ~6 months in ordinary jute/poly sack storage before
    quality/pest risk becomes a concern in humid conditions - this is the
    pack's bottleneck component, and the reason a whole delivery of packs
    gets pulled together roughly on a 6-month clock even though everything
    else inside lasts far longer.
    https://agris.fao.org/search/fr/records/6471cc8277fd37171a6fa218

  Original Creamer, 1 pack    ~18 months (545 days)
    Unopened powdered non-dairy creamer stays at best quality ~18-24 months
    at room temperature; 545 days picked at the lower end of that range.
    https://www.stilltasty.com/fooditems/index/16930

  Canned Tuna, 5 pcs          ~3 years   (1095 days)
  Canned Sardines, 2 pcs      ~3 years   (1095 days)
    Canned fish (tuna/sardines) commonly carries a 3-year shelf life after
    the code/production date.
    https://tonnino.com/blog/canned-seafood-shelf-life-what-you-need-to-know/

  Corned Beef, 4 pcs          ~2 years   (730 days)
    Low-acid canned meats (beef/chicken/pork) run 2-3 years after the code
    date; 730 days picked at the lower end of that range.
    https://www.safecastle.com/blogs/safecastle-blog/how-long-does-canned-food-last-complete-shelf-life-guide

  Ovaltine, 6 pcs             ~18 months (540 days)
    Malt drink powder is commonly rated ~2 years; 540 days matches a
    specific manufacturer-listed shelf life for a comparable product
    (Ovaltine Rich Chocolate Mix).
    https://gethuman.com/customer-service/Ovaltine/faq/What-is-the-shelf-life-of-Ovaltine/KzmyzH

Each office's batches are split with the same received-date spread used
before (already-expired / near-expiry / two fresher tranches) so the demo
still shows every shelf-life state, but now every batch also carries a full
per-component breakdown - and its overall expiration is always driven by
the rice, matching how _create_food_pack_batch works for real activity from
here on (see app.routes.pswdo._create_food_pack_batch).

Safe to re-run: exits early if any FoodPackBatch rows already exist. To
reseed with the new per-component model after the single-date version from
before this script existed, delete existing FoodPackBatch rows (cascades
nothing automatically - also delete FoodPackBatchItem rows for those
batches) first.

Usage:
    .venv/Scripts/python.exe scripts/seed_food_pack_batches.py
"""
import sys
import os
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.timezone import ph_today

from app import create_app
from app.extensions import db
from app.models.office import Office
from app.models.warehouse import WarehouseInventory
from app.models.food_pack_batch import FoodPackComponent, FoodPackBatch
from app.models.user import User
from app.routes.pswdo import _create_food_pack_batch

app = create_app()

# (name, quantity_label, shelf_life_days) - sourcing notes in the module docstring.
COMPONENTS = [
    ("Rice (Bigas)", "1 sack", 180),
    ("Original Creamer", "1 pack", 545),
    ("Canned Tuna", "5 pcs", 1095),
    ("Canned Sardines", "2 pcs", 1095),
    ("Corned Beef", "4 pcs", 730),
    ("Ovaltine", "6 pcs", 540),
]

# (share of the office's on-hand quantity, days_ago received)
# The rice (shortest shelf life, 180 days) drives each batch's overall
# expiration - so a batch received 210 days ago is already expired, one
# received 150 days ago is inside the 30-day near-expiry window, and the
# other two are still fresh even on the rice alone.
BATCH_PLAN = [
    (0.10, 210),   # rice already expired 30 days ago - drives the demo's expired/disposal flow
    (0.15, 165),   # rice expires in 15 days - inside the near-expiry window
    (0.35, 60),    # fresh
    (0.40, 10),    # freshest
]


def seed_components():
    if FoodPackComponent.query.first():
        return
    for order, (name, label, shelf_life) in enumerate(COMPONENTS, start=1):
        db.session.add(FoodPackComponent(
            name=name, quantity_label=label, shelf_life_days=shelf_life, sort_order=order
        ))
    db.session.flush()
    print(f"Seeded {len(COMPONENTS)} FoodPackComponent catalog rows.")


def run():
    with app.app_context():
        seed_components()
        component_count = FoodPackComponent.query.count()

        if FoodPackBatch.query.first():
            db.session.commit()
            print("FoodPackBatch rows already present - skipping batch backfill. "
                  "Delete existing FoodPackBatch/FoodPackBatchItem rows first if you want to reseed those.")
            return

        admin = User.query.filter_by(role="system_admin").first()
        today = ph_today()
        seeded = 0

        for office in Office.query.all():
            fp = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
            qty = fp.quantity_available if fp else 0
            if not qty:
                print(f"No Food Packs on hand at {office.office_name}, skipping")
                continue

            shares = [round(qty * pct) for pct, _ in BATCH_PLAN]
            shares[-1] += qty - sum(shares)  # remainder goes to the freshest batch

            for (_, days_ago), amount in zip(BATCH_PLAN, shares):
                if amount <= 0:
                    continue
                received_date = today - timedelta(days=days_ago)
                _create_food_pack_batch(
                    office.office_id, amount, received_date,
                    updated_by=admin.user_id if admin else None,
                )
                seeded += 1

            print(f"Seeded {len(shares)} batches for {office.office_name} ({qty:,} packs)")

        db.session.commit()
        print(f"\nSeed complete. {seeded} FoodPackBatch rows added (each with "
              f"{component_count} FoodPackBatchItem components).")
        print("Open a Municipal/Warehouse Inventory page to trigger the first "
              "expiry sync and see the expired batch (rice past its date) move "
              "into Food Packs (Expired).")


if __name__ == "__main__":
    run()
