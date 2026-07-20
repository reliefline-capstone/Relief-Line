"""
Seeds synthetic Relief Request data (CSWDO/MSWDO "Relief Requests" module)
for Santa Barbara MSWDO, covering every display state the UI needs to show:
a draft, an under-review request, an approved one (with a distribution
already scheduled), a rejected one, and two historical delivered requests
under past (ended) typhoon events for the History tab.

Verifies a couple more Santa Barbara barangay reports first (Hacienda,
Bungallon, Carosucan Sur) so there's a big enough pool of "newly verified,
not yet requested" barangays to split across the demo batches without
colliding with the Calepaan/Coliling/Ban-ao allocations seed_demo_data.py
already created for the active event.

Safe to re-run: exits early if any ReliefRequestBatch rows already exist.

Usage:
    .venv/Scripts/python.exe scripts/seed_relief_requests.py
"""
import sys
import os
from datetime import date, datetime, timedelta, time as dtime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.office import Office
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.barangay_report import BarangayReport
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.relief_request_batch import ReliefRequestBatch
from app.models.user import User
from app.ml import predict as ml_predict

app = create_app()

LGU = "Santa Barbara"


def _predict(barangay):
    return ml_predict.predict_quantity(barangay) or (barangay.population or 0) // 20


def run():
    with app.app_context():
        if ReliefRequestBatch.query.first():
            print("ReliefRequestBatch rows already present — skipping. "
                  "Delete existing rows first if you want to reseed.")
            return

        today = date.today()
        barangays = {b.barangay_name: b for b in Barangay.query.filter_by(city_municipality=LGU).all()}
        office = Office.query.filter_by(office_type="cswdo", area_covered=LGU).first()
        warehouse_a = Office.query.filter_by(office_name="Warehouse A").first()
        cswdo_admin = User.query.filter_by(office_id=office.office_id, role="cswdo_admin").first()
        pswdo_admin = User.query.filter_by(role="pswdo_admin").first()

        active_event = DisasterEvent.query.filter_by(status="active").order_by(
            DisasterEvent.start_date.desc()
        ).first()
        if not active_event:
            print("No active DisasterEvent found — run seed_demo_data.py first.")
            return

        # --- Verify a few more Santa Barbara reports so there's enough of an
        # eligible pool to split across the demo batches below ---
        def _verify(name, families, individuals):
            b = barangays[name]
            report = BarangayReport.query.filter_by(barangay_id=b.barangay_id, event_id=active_event.event_id).first()
            if not report:
                report = BarangayReport(
                    barangay_id=b.barangay_id, event_id=active_event.event_id,
                    submitted_by_name="Barangay Office", submitted_by_designation="Barangay Secretary",
                    affected_families=families, affected_individuals=individuals,
                    totally_damaged_houses=max(families // 20, 1), partially_damaged_houses=max(families // 12, 1),
                    flood_level="needs_assistance", flood_depth_m=0.5,
                    remarks="Seeded for Relief Requests demo.",
                    photo_paths=f"photo_{name.lower().replace(' ', '_')}_1.jpg",
                )
                db.session.add(report)
            report.status = "verified"
            report.affected_families = families
            report.affected_individuals = individuals
            report.review_remarks = report.review_remarks or "Verified for relief request demo."
            report.reviewed_by = cswdo_admin.user_id if cswdo_admin else None
            report.reviewed_at = datetime.utcnow()

            status_row = BarangayDisasterStatus.query.filter_by(barangay_id=b.barangay_id, event_id=active_event.event_id).first()
            if status_row:
                status_row.status = report.flood_level
                status_row.affected_families = families
            else:
                db.session.add(BarangayDisasterStatus(
                    barangay_id=b.barangay_id, event_id=active_event.event_id,
                    status=report.flood_level, affected_families=families,
                    updated_by=cswdo_admin.user_id if cswdo_admin else None,
                ))
            db.session.flush()
            return report

        _verify("Hacienda", 340, 1360)
        _verify("Bungallon", 210, 840)
        _verify("Carosucan Sur", 175, 700)
        db.session.flush()
        print("Verified Hacienda, Bungallon, Carosucan Sur for the active event")

        def _already_requested(barangay_id, event_id):
            return AllocationRecord.query.filter_by(barangay_id=barangay_id, event_id=event_id).first() is not None

        def make_batch(barangay_names, requested_packs, priority, reason, remarks,
                        days_ago, decision=None, rejection_reason=None,
                        distribution_stage=None, event=None):
            """decision: None (pending), 'approved', or 'rejected'.
            distribution_stage: None, or a DistributionRecord.dispatch_status value."""
            ev = event or active_event
            submitted_at = datetime.utcnow() - timedelta(days=days_ago)
            batch = ReliefRequestBatch(
                office_id=office.office_id, event_id=ev.event_id,
                requested_food_packs=requested_packs, priority=priority,
                reason=reason, remarks=remarks,
                created_by=cswdo_admin.user_id if cswdo_admin else None,
                created_at=submitted_at, submitted_at=submitted_at,
            )
            db.session.add(batch)
            db.session.flush()

            names = [n for n in barangay_names if not _already_requested(barangays[n].barangay_id, ev.event_id)]
            predictions = {n: _predict(barangays[n]) for n in names}
            model_total = sum(predictions.values()) or 1

            for n in names:
                b = barangays[n]
                qty = round(predictions[n] / model_total * requested_packs) if model_total else requested_packs // len(names)
                alloc = AllocationRecord(
                    barangay_id=b.barangay_id, office_id=office.office_id,
                    predicted_quantity=max(qty, 1), allocation_date=submitted_at.date(),
                    event_id=ev.event_id, created_by=cswdo_admin.user_id if cswdo_admin else None,
                    batch_id=batch.batch_id,
                )
                if decision == "approved":
                    alloc.status = "approved"
                    alloc.allocated_quantity = alloc.predicted_quantity
                    alloc.fulfilling_office_id = warehouse_a.office_id if warehouse_a else None
                    alloc.expected_delivery_date = submitted_at.date() + timedelta(days=2)
                    alloc.decided_by = pswdo_admin.user_id if pswdo_admin else None
                elif decision == "rejected":
                    alloc.rejection_reason = rejection_reason or "Insufficient supporting documentation."
                    alloc.decided_by = pswdo_admin.user_id if pswdo_admin else None
                db.session.add(alloc)
                db.session.flush()

                if distribution_stage:
                    db.session.add(DistributionRecord(
                        barangay_id=b.barangay_id, allocation_id=alloc.allocation_id,
                        quantity_released=alloc.allocated_quantity, distribution_date=today,
                        dispatch_status=distribution_stage,
                        vehicle_id=None, driver_id=None,
                        departure_time=dtime(8, 0), expected_arrival_time=dtime(11, 0),
                        status="confirmed" if distribution_stage == "delivered" else "pending",
                        submitted_by=pswdo_admin.user_id if pswdo_admin else None,
                        received_by="Barangay Officer" if distribution_stage == "delivered" else None,
                        condition="complete" if distribution_stage == "delivered" else None,
                    ))
            db.session.flush()
            return batch

        # --- Draft: no AllocationRecords, doesn't lock any barangay ---
        draft = ReliefRequestBatch(
            office_id=office.office_id, event_id=active_event.event_id,
            requested_food_packs=600, priority="medium",
            reason="", remarks="",
            created_by=cswdo_admin.user_id if cswdo_admin else None,
        )
        db.session.add(draft)

        # --- Under Review: Hacienda (still pending PSWDO decision) ---
        make_batch(
            ["Hacienda"], requested_packs=1500, priority="high",
            reason="Rising floodwater near the irrigation canal is displacing households; requesting priority food pack allocation.",
            remarks="", days_ago=1,
        )

        # --- Approved: Mapolopolo + Abot, PSWDO approved, preparing distribution ---
        make_batch(
            ["Mapolopolo", "Abot"], requested_packs=900, priority="medium",
            reason="Verified barangay reports show sustained flooding; requesting food packs to cover the affected families.",
            remarks="Please prioritize Abot given the higher affected household count.",
            days_ago=3, decision="approved", distribution_stage="preparing",
        )

        # --- Rejected: Bungallon + Carosucan Sur ---
        make_batch(
            ["Bungallon", "Carosucan Sur"], requested_packs=700, priority="low",
            reason="Minor flooding reported; requesting food packs as a precaution.",
            remarks="", days_ago=4, decision="rejected",
            rejection_reason="Insufficient damage report documentation. Please resubmit with complete barangay verification.",
        )

        db.session.flush()
        print("Seeded 1 draft + 3 submitted batches (under review / approved / rejected) for the active event")

        # --- History: 2 ended events with fully delivered requests ---
        dante = DisasterEvent.query.filter_by(event_name="Typhoon Dante").first()
        if not dante:
            dante = DisasterEvent(
                event_name="Typhoon Dante", event_type="typhoon", status="ended",
                weather_condition="Cleared", start_date=today - timedelta(days=395),
                end_date=today - timedelta(days=390),
                created_by=pswdo_admin.user_id if pswdo_admin else None,
            )
            db.session.add(dante)
            db.session.flush()

        egay = DisasterEvent.query.filter_by(event_name="Typhoon Egay").first()
        if not egay:
            egay = DisasterEvent(
                event_name="Typhoon Egay", event_type="typhoon", status="ended",
                weather_condition="Cleared", start_date=today - timedelta(days=435),
                end_date=today - timedelta(days=430),
                created_by=pswdo_admin.user_id if pswdo_admin else None,
            )
            db.session.add(egay)
            db.session.flush()

        make_batch(
            ["Batayang", "Carosucan Norte"], requested_packs=900, priority="medium",
            reason="Post-typhoon flooding required food pack assistance for the two barangays.",
            remarks="", days_ago=390, decision="approved", distribution_stage="delivered",
            event=dante,
        )
        make_batch(
            ["Ban-ao", "Coliling", "Calepaan"], requested_packs=1200, priority="high",
            reason="Widespread flooding across three barangays required urgent food pack support.",
            remarks="", days_ago=430, decision="approved", distribution_stage="delivered",
            event=egay,
        )

        db.session.commit()
        print("Seeded 2 historical delivered batches (Typhoon Dante, Typhoon Egay)")
        print("\nSeed complete.")


if __name__ == "__main__":
    run()
