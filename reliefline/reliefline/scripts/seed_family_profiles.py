"""
Seeds every barangay with a synthetic Family Profiles registry - the
household checklist a Barangay Report is now built from (panelist-requested
"profiling" feature; see app/models/family.py and
app.routes.barangay._apply_affected_families).

Real profiling data hasn't arrived yet (see [[model-retrain-pending-real-
datasets]] in project memory), so this generates a plausible sample per
barangay - proportional to Barangay.num_households but capped, since seeding
every one of Pangasinan's 70k+ actual households would be excessive for a
demo - with randomized member/PWD/senior/children counts.

Safe to re-run: exits early if any Family row already exists. To reseed,
delete existing rows first:
    DELETE FROM barangay_report_families; DELETE FROM barangay_families;

Usage:
    .venv/Scripts/python.exe scripts/seed_family_profiles.py
"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.family import Family

app = create_app()

random.seed(20260911)  # reproducible demo data

SURNAMES = [
    "Dela Cruz", "Reyes", "Santos", "Garcia", "Mendoza", "Ramos", "Torres",
    "Flores", "Villanueva", "Castillo", "Aquino", "Bautista", "Del Rosario",
    "Manalo", "Fernandez", "Pascual", "Domingo", "Salazar", "Navarro",
    "Rivera", "Gonzales", "Aguilar", "Marquez", "Cruz", "Soriano", "Ocampo",
    "Corpuz", "Lacson", "Valdez", "Espino", "Fabian", "Sison", "Rosario",
    "Molina", "Ferrer",
]
FIRST_NAMES = [
    "Juan", "Maria", "Jose", "Ana", "Pedro", "Rosa", "Carlos", "Elena",
    "Ramon", "Corazon", "Antonio", "Luz", "Ricardo", "Teresa", "Eduardo",
    "Linda", "Fernando", "Grace", "Manuel", "Josefa", "Roberto", "Cynthia",
    "Danilo", "Imelda",
]
PUROKS = ["Purok 1", "Purok 2", "Purok 3", "Purok 4", "Purok 5", "Purok 6", "Sitio Ilog", "Sitio Bukid"]

MIN_FAMILIES_PER_BARANGAY = 15
MAX_FAMILIES_PER_BARANGAY = 35


def _family_count_for(barangay):
    # Proportional to num_households (bigger barangay -> a slightly bigger
    # sample), but capped so the registry stays a browsable demo checklist
    # rather than a full census.
    scale = min(1.0, (barangay.num_households or 0) / 2000)
    target = MIN_FAMILIES_PER_BARANGAY + round(scale * (MAX_FAMILIES_PER_BARANGAY - MIN_FAMILIES_PER_BARANGAY))
    return target


def _random_family(barangay_id, purok):
    # member_count skewed around 4-5 (PSA average Filipino household size),
    # occasionally larger.
    member_count = random.choices([2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[8, 14, 20, 20, 16, 10, 6, 3, 3])[0]

    # ~30% of families have at least one senior; ~15% have at least one PWD.
    senior_count = 0
    if random.random() < 0.30:
        senior_count = min(member_count, random.choices([1, 2], weights=[80, 20])[0])
    pwd_count = 0
    if random.random() < 0.15:
        pwd_count = min(member_count, 1)
    # Children (under 18) - roughly a third of the household on average, at
    # least for larger families.
    max_children = max(0, member_count - senior_count - 1)
    children_count = min(max_children, random.randint(0, max(0, member_count // 2)))

    # family_name is always just "{Surname} Family" - the primary display.
    # head_name (the actual head-of-household's given name) is a secondary/
    # subtitle field, shown smaller underneath - it's what actually tells
    # apart two families that share both a surname and a purok, not a
    # "(2)" suffix on the primary label.
    surname = random.choice(SURNAMES)

    return Family(
        barangay_id=barangay_id,
        family_name=f"{surname} Family",
        head_name=random.choice(FIRST_NAMES),
        purok=purok,
        contact_number=f"09{random.randint(100000000, 999999999)}",
        member_count=member_count,
        pwd_count=pwd_count,
        senior_count=senior_count,
        children_count=children_count,
    )


def run():
    with app.app_context():
        if Family.query.first():
            print("Family profiles already present - skipping. Delete existing rows first if you want to reseed.")
            return

        barangays = Barangay.query.all()
        total = 0
        for barangay in barangays:
            count = _family_count_for(barangay)
            for _ in range(count):
                purok = random.choice(PUROKS)
                db.session.add(_random_family(barangay.barangay_id, purok))
            total += count
        db.session.commit()
        print(f"Seeded {total} synthetic family profiles across {len(barangays)} barangays "
              f"({MIN_FAMILIES_PER_BARANGAY}-{MAX_FAMILIES_PER_BARANGAY} each).")


if __name__ == "__main__":
    run()
