"""
Seeds synthetic "donation" WarehouseStockLog entries so the Stock Movement
History page (and the Recent Movements panels on the Dashboard / Warehouse
Detail pages) has real donation-tagged entries to show — see the Source
field added to Warehouse Inventory's Add Stock / Update Stock modals
(source_type="standard"|"donation", donor_name).

Also seeds a couple of plain "standard" restocks alongside the donations so
the movement history reads as a realistic mix, not an all-donation feed.

Each entry both inserts a WarehouseStockLog row AND increases the matching
WarehouseInventory.quantity_available by the same delta, so the current
on-hand totals shown elsewhere in the app (dashboard stat cards, GIS map
hover, warehouse inventory tables) stay internally consistent with the
movement history that explains them.

Safe to re-run: exits early if any donation-tagged WarehouseStockLog rows
already exist.

Usage:
    .venv/Scripts/python.exe scripts/seed_donation_stock.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.office import Office
from app.models.warehouse import WarehouseInventory, WarehouseStockLog
from app.models.user import User

app = create_app()

# (office_name, item_type, delta, source_type, donor_name, reason, days_ago)
ENTRIES = [
    ("Provincial Social Welfare and Development Office", "food_pack", 1500,
     "donation", "Philippine Red Cross", "Typhoon relief donation drive", 9),
    ("Provincial Social Welfare and Development Office", "hygiene_kit", 300,
     "donation", "DSWD Central Office", "National office augmentation for hygiene kit stock", 7),
    ("PSWDO Warehouse", "food_pack", 2000,
     "donation", "Jollibee Group Foundation, Inc.", "Corporate relief drive donation", 6),
    ("Urdaneta City Social Welfare and Development Office", "food_pack", 300,
     "donation", "SM Foundation", "Typhoon relief donation drive", 5),
    ("Santa Barbara Municipal Social Welfare and Development Office", "kitchen_kit", 50,
     "donation", "Rotary Club of Pangasinan", "Local civic group donation", 4),
    ("Calasiao Municipal Social Welfare and Development Office", "food_pack", 400,
     "donation", "Ayala Foundation", "Typhoon relief donation drive", 3),
    # Plain restocks alongside the donations, so the movement feed reads as a
    # realistic mix rather than looking artificially all-donation.
    ("PSWDO Warehouse", "food_pack", 3000,
     "standard", None, "Provincial budget replenishment", 8),
    ("Urdaneta City Social Welfare and Development Office", "hygiene_kit", 150,
     "standard", None, "Routine restock from provincial supply", 2),
]


def run():
    with app.app_context():
        if WarehouseStockLog.query.filter_by(source_type="donation").first():
            print("Donation-tagged WarehouseStockLog rows already present — skipping. "
                  "Delete existing donation rows first if you want to reseed.")
            return

        pswdo_admin = User.query.filter_by(role="pswdo_admin").first() or User.query.filter_by(role="system_admin").first()
        now = datetime.utcnow()
        seeded = 0

        for office_name, item_type, delta, source_type, donor_name, reason, days_ago in ENTRIES:
            office = Office.query.filter_by(office_name=office_name).first()
            if not office:
                print(f"Office not found, skipping: {office_name}")
                continue

            item = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type=item_type).first()
            if not item:
                print(f"No {item_type} inventory row at {office_name}, skipping")
                continue

            item.quantity_available = (item.quantity_available or 0) + delta

            db.session.add(WarehouseStockLog(
                office_id=office.office_id, item_type=item_type, item_name=item.item_name,
                delta=delta, reason=reason, source_type=source_type, donor_name=donor_name,
                updated_by=pswdo_admin.user_id if pswdo_admin else None,
                created_at=now - timedelta(days=days_ago),
            ))
            seeded += 1
            label = f"donation from {donor_name}" if source_type == "donation" else "standard restock"
            print(f"+{delta:,} {item.item_name} at {office_name} ({label})")

        db.session.commit()
        print(f"\nSeed complete. {seeded} WarehouseStockLog entries added.")


if __name__ == "__main__":
    run()
