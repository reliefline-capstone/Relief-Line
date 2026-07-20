"""
Seeds synthetic BarangayReport rows (Damage Assessment module) for the 3
target LGUs, tied to the active disaster event. Where a barangay already has
a BarangayDisasterStatus row from seed_demo_data.py, the matching report is
seeded as already "verified" with the same flood_level/affected_families, so
verifying it in the UI doesn't contradict data already shown on the
dashboard/GIS map. A couple of barangays per LGU are left with no report at
all, to exercise the "no report submitted yet" state.

Safe to re-run: exits early if any BarangayReport rows already exist.

Usage:
    .venv/Scripts/python.exe scripts/seed_barangay_reports.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.disaster_event import DisasterEvent
from app.models.barangay_report import BarangayReport
from app.models.barangay_status import BarangayDisasterStatus
from app.models.user import User

app = create_app()

# (barangay_name, submitted_by_name, designation, status, flood_level, families,
#  individuals, totally_damaged, partially_damaged, flood_depth_m, remarks,
#  review_remarks, hours_ago_submitted)
PLAN = {
    "Santa Barbara": [
        ("Abot", "Ricardo Manalo", "Barangay Captain", "pending", "monitoring", 150, 600, 2, 5, 0.3,
         "Light flooding along the creek. Monitoring water level.", None, 3),
        ("Ban-ao", "Corazon Dizon", "Barangay Secretary", "verified", "monitoring", 300, 1200, 4, 9, 0.4,
         "Flooding receding. Residents advised to stay alert.", "Consistent with barangay visit.", 6),
        ("Batayang", "Ernesto Villar", "Barangay Kagawad", "pending", "needs_assistance", 220, 880, 9, 14, 0.6,
         "Several households still without power.", None, 2),
        # Bungallon — no report submitted yet
        ("Calepaan", "Marissa Ocampo", "Barangay Captain", "verified", "high_priority", 900, 3600, 22, 31, 1.1,
         "Critical flooding, main road impassable.", "Verified on-site. Matches CDRRMO advisory.", 8),
        ("Carosucan Norte", "Danilo Ferrer", "Barangay Secretary", "returned", "normal", 80, 320, 0, 3, 0.1,
         "Minor debris on roadside only.", "Please confirm affected-families count — seems too high for the reported damage.", 5),
        # Carosucan Sur — no report submitted yet
        ("Coliling", "Teresita Bautista", "Barangay Captain", "verified", "needs_assistance", 600, 2400, 11, 19, 0.7,
         "Several families relocated to higher ground.", "Verified. Data consistent with field visit.", 7),
        ("Hacienda", "Romeo Castillo", "Barangay Kagawad", "pending", "high_priority", 340, 1360, 15, 20, 0.9,
         "Rising water level near the irrigation canal.", None, 1),
        ("Mapolopolo", "Luz Aquino", "Barangay Secretary", "verified", "normal", 40, 160, 0, 1, 0.0,
         "No significant impact observed.", "Verified.", 9),
    ],
    "Urdaneta City": [
        ("Anonas", "Julieta Reyes", "Barangay Captain", "verified", "high_priority", 1200, 4800, 28, 40, 1.3,
         "Critical flooding, evacuation ongoing.", "Verified on-site — matches CDRRMO report.", 10),
        ("Bactad East", "Mario Corpuz", "Barangay Secretary", "verified", "needs_assistance", 800, 3200, 14, 22, 0.8,
         "Flood waters entering low-lying homes.", "Consistent with field visit.", 9),
        ("Bayaoas", "Angelita Ramos", "Barangay Kagawad", "pending", "monitoring", 180, 720, 3, 6, 0.3,
         "Water level rising slowly, monitoring situation.", None, 2),
        ("Bolaoen", "Feliciano Domingo", "Barangay Captain", "pending", "normal", 60, 240, 0, 2, 0.0,
         "No flooding reported, strong winds only.", None, 4),
        ("Cabaruan", "Yolanda Santiago", "Barangay Secretary", "verified", "needs_assistance", 600, 2400, 10, 18, 0.6,
         "Several roads temporarily flooded.", "Verified. Redirect relief coordination noted.", 11),
        # Cabuloan — no report submitted yet
        ("Camantiles", "Arnel Pascual", "Barangay Kagawad", "returned", "monitoring", 95, 380, 1, 3, 0.2,
         "Minor flooding near the barangay hall.", "Photo evidence unclear — please resubmit with a clearer shot.", 3),
        ("Casantaan", "Remedios Torres", "Barangay Captain", "pending", "needs_assistance", 260, 1040, 8, 13, 0.7,
         "Creek overflowed near residential area.", None, 1),
        # Catablan — no report submitted yet
        ("Cayambanan", "Benjamin Aguilar", "Barangay Secretary", "pending", "monitoring", 130, 520, 2, 5, 0.3,
         "Light flooding, situation stable.", None, 5),
    ],
    "Calasiao": [
        ("Ambonao", "Perlita Navarro", "Barangay Captain", "pending", "monitoring", 140, 560, 2, 4, 0.3,
         "Light flooding along the main road.", None, 2),
        ("Ambuetel", "Josefina Mendoza", "Barangay Secretary", "returned", "normal", 50, 200, 0, 1, 0.0,
         "No significant damage observed.", "Report is missing barangay captain's signature — please resubmit.", 4),
        ("Banaoang", "Ramon Salvador", "Barangay Kagawad", "verified", "monitoring", 250, 1000, 3, 7, 0.3,
         "Flooding receding along riverside homes.", "Verified. Matches previous advisory.", 8),
        ("Bued", "Cristina Lopez", "Barangay Captain", "pending", "needs_assistance", 210, 840, 7, 12, 0.6,
         "Rising water level near the river bank.", None, 1),
        ("Buenlag", "Fernando Garcia", "Barangay Secretary", "pending", "normal", 70, 280, 0, 2, 0.0,
         "Strong winds, no flooding reported.", None, 6),
        ("Cabilocaan", "Aurora Ramirez", "Barangay Kagawad", "verified", "needs_assistance", 500, 2000, 9, 16, 0.6,
         "Several families temporarily relocated.", "Verified on-site.", 9),
        # Dinalaoan — no report submitted yet
        ("Doyong", "Salvador Cruz", "Barangay Captain", "verified", "monitoring", 350, 1400, 4, 8, 0.4,
         "Water receding, roads passable.", "Verified.", 10),
        # Gabon — no report submitted yet
        ("Lasip", "Herminia Flores", "Barangay Secretary", "verified", "high_priority", 700, 2800, 18, 25, 1.0,
         "Critical flooding, several households isolated.", "Verified — matches CDRRMO advisory.", 12),
    ],
}


def run():
    with app.app_context():
        if BarangayReport.query.first():
            print("BarangayReport rows already present — skipping. "
                  "Delete existing rows first if you want to reseed.")
            return

        event = DisasterEvent.query.filter_by(status="active").order_by(
            DisasterEvent.start_date.desc()
        ).first()
        if not event:
            print("No active DisasterEvent found — run seed_demo_data.py first.")
            return

        reviewers = {u.office_id: u for u in User.query.filter_by(role="cswdo_admin").all()}
        now = datetime.utcnow()
        count = 0

        for lgu, rows in PLAN.items():
            barangays = {b.barangay_name: b for b in Barangay.query.filter_by(city_municipality=lgu).all()}
            for (name, submitter, designation, status, flood_level, families, individuals,
                 totally_damaged, partially_damaged, depth, remarks, review_remarks, hours_ago) in rows:
                barangay = barangays.get(name)
                if not barangay:
                    print(f"  WARNING: barangay '{name}' not found under {lgu}, skipping")
                    continue

                report = BarangayReport(
                    barangay_id=barangay.barangay_id,
                    event_id=event.event_id,
                    submitted_by_name=submitter,
                    submitted_by_designation=designation,
                    submitted_at=now - timedelta(hours=hours_ago),
                    affected_families=families,
                    affected_individuals=individuals,
                    totally_damaged_houses=totally_damaged,
                    partially_damaged_houses=partially_damaged,
                    flood_level=flood_level,
                    flood_depth_m=depth,
                    remarks=remarks,
                    photo_paths=f"photo_{barangay.barangay_name.lower().replace(' ', '_')}_1.jpg",
                    status=status,
                )

                office_reviewer = next(
                    (u for u in reviewers.values() if u.office and u.office.area_covered == lgu), None
                )
                if status in ("verified", "returned"):
                    report.review_remarks = review_remarks
                    report.reviewed_by = office_reviewer.user_id if office_reviewer else None
                    report.reviewed_at = now - timedelta(hours=max(hours_ago - 1, 0))

                db.session.add(report)
                count += 1

                # Keep BarangayDisasterStatus in sync for already-verified reports,
                # same upsert the "Verify Report" action performs at runtime.
                if status == "verified":
                    existing = BarangayDisasterStatus.query.filter_by(
                        barangay_id=barangay.barangay_id, event_id=event.event_id
                    ).first()
                    if existing:
                        existing.status = flood_level
                        existing.affected_families = families
                    else:
                        db.session.add(BarangayDisasterStatus(
                            barangay_id=barangay.barangay_id, event_id=event.event_id,
                            status=flood_level, affected_families=families,
                            updated_by=office_reviewer.user_id if office_reviewer else None,
                        ))

        db.session.commit()
        print(f"Seeded {count} BarangayReport rows across {len(PLAN)} LGUs.")


if __name__ == "__main__":
    run()
