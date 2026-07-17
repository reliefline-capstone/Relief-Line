"""
Populates ReliefLine's dev database with realistic demo data spanning the
dashboard, relief requests, and distribution operations pages: barangay
disaster statuses (drives Priority/Affected Families), allocation requests in
every status (pending/approved/partially approved/rejected), a vehicle/driver
fleet, and distribution records covering every dispatch stage (preparing,
loaded, dispatched, in transit, delivered, delayed).

Safe to re-run: exits early if demo data already appears to be present
(checks for a "Truck 001" vehicle). To reset, delete the seeded rows first
(see the bottom of this file for the exact tables touched).

Usage:
    .venv/Scripts/python.exe scripts/seed_demo_data.py
"""
import sys
import os
from datetime import date, timedelta, time as dtime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.office import Office
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.logistics import Vehicle, Driver
from app.models.warehouse import WarehouseInventory
from app.models.activity_log import ActivityLog, DailyOpsStat
from app.models.user import User

app = create_app()

TARGET_LGUS = ["Urdaneta City", "Santa Barbara", "Calasiao"]


def run():
    with app.app_context():
        if Vehicle.query.filter_by(vehicle_name="Truck 001").first():
            print("Demo data already present (found 'Truck 001') — skipping. "
                  "Delete existing rows first if you want to reseed.")
            return

        today = date.today()
        barangays = {b.barangay_name: b for b in Barangay.query.filter(
            Barangay.city_municipality.in_(TARGET_LGUS)
        ).all()}
        muni_offices = {o.area_covered: o for o in Office.query.filter_by(office_type="cswdo").all()}
        warehouse_a = Office.query.filter_by(office_name="Warehouse A").first()
        admin_users = {u.role: u for u in User.query.all()}
        pswdo_admin = admin_users.get("pswdo_admin") or admin_users.get("system_admin")

        event = DisasterEvent.query.filter_by(status="active").order_by(DisasterEvent.start_date.desc()).first()
        if not event:
            event = DisasterEvent(
                event_name="Typhoon Crising", event_type="typhoon", status="active",
                weather_condition="Thunderstorm", start_date=today - timedelta(days=7),
                created_by=pswdo_admin.user_id if pswdo_admin else None,
            )
            db.session.add(event)
            db.session.flush()
        print(f"Using event: {event.event_name} (id={event.event_id})")

        # --- Warehouse A stock: give it real, non-zero inventory to fulfill demo allocations ---
        wa_inventory = WarehouseInventory.query.filter_by(office_id=warehouse_a.office_id, item_type="food_pack").first()
        if not wa_inventory:
            wa_inventory = WarehouseInventory(office_id=warehouse_a.office_id, item_type="food_pack",
                                               quantity_available=22000, min_stock_level=3000)
            db.session.add(wa_inventory)
        else:
            wa_inventory.quantity_available = 22000
        db.session.flush()

        # --- Barangay disaster statuses (drives Priority + Affected Families everywhere) ---
        status_plan = [
            ("Anonas", "high_priority", 1200),
            ("Bactad East", "needs_assistance", 800),
            ("Bayaoas", "monitoring", 400),
            ("Cabaruan", "needs_assistance", 600),
            ("Calepaan", "high_priority", 900),
            ("Coliling", "needs_assistance", 600),
            ("Ban-ao", "monitoring", 300),
            ("Lasip", "high_priority", 700),
            ("Cabilocaan", "needs_assistance", 500),
            ("Doyong", "monitoring", 350),
            ("Banaoang", "monitoring", 250),
        ]
        for name, status, families in status_plan:
            b = barangays[name]
            existing = BarangayDisasterStatus.query.filter_by(barangay_id=b.barangay_id, event_id=event.event_id).first()
            if not existing:
                db.session.add(BarangayDisasterStatus(
                    barangay_id=b.barangay_id, event_id=event.event_id,
                    status=status, affected_families=families,
                    updated_by=pswdo_admin.user_id if pswdo_admin else None,
                ))
        db.session.flush()
        print(f"Seeded {len(status_plan)} BarangayDisasterStatus rows")

        # --- Vehicles & drivers (Warehouse A's fleet) ---
        vehicles = {
            "Truck 001": Vehicle(vehicle_name="Truck 001", plate_number="ABC-1234", capacity_packs=2000, office_id=warehouse_a.office_id),
            "Truck 002": Vehicle(vehicle_name="Truck 002", plate_number="DEF-5678", capacity_packs=1500, office_id=warehouse_a.office_id),
            "Truck 003": Vehicle(vehicle_name="Truck 003", plate_number="GHI-9012", capacity_packs=1800, office_id=warehouse_a.office_id),
        }
        db.session.add_all(vehicles.values())

        drivers = {
            "Juan Dela Cruz": Driver(name="Juan Dela Cruz", office_id=warehouse_a.office_id),
            "Pedro Santos": Driver(name="Pedro Santos", office_id=warehouse_a.office_id),
            "Mark Reyes": Driver(name="Mark Reyes", office_id=warehouse_a.office_id),
        }
        db.session.add_all(drivers.values())
        db.session.flush()
        print("Seeded 3 vehicles and 3 drivers")

        def make_allocation(barangay_name, muni, predicted, alloc_status, allocated=0,
                             expected_delivery_days=2, rejection_reason=None):
            b = barangays[barangay_name]
            office = muni_offices[muni]
            alloc = AllocationRecord(
                barangay_id=b.barangay_id, office_id=office.office_id,
                predicted_quantity=predicted, allocated_quantity=allocated,
                allocation_date=today - timedelta(days=1), event_id=event.event_id,
                status=alloc_status,
            )
            if alloc_status == "approved":
                alloc.fulfilling_office_id = warehouse_a.office_id
                alloc.expected_delivery_date = today + timedelta(days=expected_delivery_days)
                alloc.decided_by = pswdo_admin.user_id if pswdo_admin else None
                alloc.created_by = pswdo_admin.user_id if pswdo_admin else None
            if rejection_reason:
                alloc.rejection_reason = rejection_reason
                alloc.decided_by = pswdo_admin.user_id if pswdo_admin else None
            db.session.add(alloc)
            db.session.flush()
            return alloc

        def make_distribution(alloc, dispatch_status, vehicle=None, driver=None,
                               departure=None, arrival=None, received_by=None,
                               condition=None, travel_time=None):
            rec = DistributionRecord(
                barangay_id=alloc.barangay_id, allocation_id=alloc.allocation_id,
                quantity_released=alloc.allocated_quantity,
                distribution_date=today, dispatch_status=dispatch_status,
                vehicle_id=vehicle.vehicle_id if vehicle else None,
                driver_id=driver.driver_id if driver else None,
                departure_time=departure, expected_arrival_time=arrival,
                received_by=received_by, condition=condition, travel_time=travel_time,
                status="confirmed" if dispatch_status == "delivered" else "pending",
                submitted_by=pswdo_admin.user_id if pswdo_admin else None,
            )
            db.session.add(rec)
            # Mirror the real approve flow's inventory deduction so numbers stay consistent
            wa_inventory.quantity_available -= alloc.allocated_quantity
            return rec

        # --- Allocations + distributions (covers every status combo) ---
        a1 = make_allocation("Anonas", "Urdaneta City", 2300, "approved", 2300)
        d1 = make_distribution(a1, "delivered", vehicles["Truck 001"], drivers["Juan Dela Cruz"],
                           dtime(8, 0), dtime(10, 30), "Aivan Flores", "complete", "2 hrs 30 mins")

        a2 = make_allocation("Bactad East", "Urdaneta City", 1500, "approved", 1500)
        d2 = make_distribution(a2, "in_transit", vehicles["Truck 002"], drivers["Pedro Santos"],
                           dtime(7, 30), dtime(9, 45))

        a3 = make_allocation("Calepaan", "Santa Barbara", 900, "approved", 900)
        make_distribution(a3, "dispatched", vehicles["Truck 003"], drivers["Mark Reyes"],
                           dtime(9, 0), dtime(11, 15))

        a4 = make_allocation("Coliling", "Santa Barbara", 600, "approved", 600)
        make_distribution(a4, "loaded", vehicles["Truck 002"], drivers["Pedro Santos"])

        a5 = make_allocation("Lasip", "Calasiao", 1800, "approved", 1800)
        make_distribution(a5, "preparing")

        a6 = make_allocation("Cabilocaan", "Calasiao", 1200, "approved", 1200)
        make_distribution(a6, "delayed")

        a7 = make_allocation("Doyong", "Calasiao", 1100, "approved", 1100)
        make_distribution(a7, "delivered", vehicles["Truck 001"], drivers["Juan Dela Cruz"],
                           dtime(6, 45), dtime(9, 0), "Maria Santos", "complete", "2 hrs 15 mins")

        make_allocation("Bayaoas", "Urdaneta City", 1000, "pending")
        make_allocation("Ban-ao", "Santa Barbara", 700, "pending")
        make_allocation("Banaoang", "Calasiao", 500, "approved", 300, expected_delivery_days=1)
        make_allocation("Cabaruan", "Urdaneta City", 800, "pending",
                         rejection_reason="Municipal warehouse already has adequate stock for this barangay; redirected to Bayaoas instead.")

        db.session.flush()
        print("Seeded 11 AllocationRecords (2 pending, 7 approved/full, 1 partial, 1 rejected)")
        print("Seeded 7 DistributionRecords covering preparing/loaded/dispatched/in_transit/delivered(x2)/delayed")

        # --- Recent activity feed ---
        activities = [
            ("allocation_approved", f"Approved 2,300 food packs for Urdaneta City from {warehouse_a.office_name}", a1.barangay_id),
            ("distribution_delivered", "D-{}-{:03d} delivered to Urdaneta City, received by Aivan Flores".format(today.year, d1.distribution_id), a1.barangay_id),
            ("allocation_approved", f"Approved 900 food packs for Santa Barbara from {warehouse_a.office_name}", a3.barangay_id),
            ("distribution_status", "Distribution marked In Transit for Bactad East, Urdaneta City", a2.barangay_id),
            ("allocation_rejected", "Rejected relief request from Urdaneta City: adequate stock on hand", barangays["Cabaruan"].barangay_id),
        ]
        for action_type, desc, b_id in activities:
            db.session.add(ActivityLog(
                actor_id=pswdo_admin.user_id if pswdo_admin else None,
                action_type=action_type, description=desc,
                office_id=warehouse_a.office_id, barangay_id=b_id,
            ))

        # --- Today's vehicle activity stat (feeds the dashboard's "Vehicles Active") ---
        for muni in TARGET_LGUS:
            office = muni_offices[muni]
            if not DailyOpsStat.query.filter_by(office_id=office.office_id, stat_date=today).first():
                db.session.add(DailyOpsStat(
                    office_id=office.office_id, stat_date=today,
                    vehicles_active=1, updated_by=pswdo_admin.user_id if pswdo_admin else None,
                ))

        db.session.commit()
        print("\nSeed complete.")
        print(f"Warehouse A food_pack stock: {wa_inventory.quantity_available:,} / 22,000 capacity")


if __name__ == "__main__":
    run()
