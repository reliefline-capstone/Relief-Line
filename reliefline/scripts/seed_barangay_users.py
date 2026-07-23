"""
Creates one barangay_user login per row in `barangays` (Table 10: "Barangay-
Level Users" — authorized barangay personnel who submit/validate relief-
related information). Every target barangay across Urdaneta City, Santa
Barbara, and Calasiao gets exactly one account, keyed off barangay_id (not
barangay_name, since names repeat across LGUs — e.g. "Banaoang" exists in
both Calasiao and Santa Barbara).

Safe to re-run: skips any barangay that already has a barangay_user account.

Usage:
    .venv/Scripts/python.exe scripts/seed_barangay_users.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.user import User

app = create_app()

DEFAULT_PASSWORD = "reliefline123"

# Deterministic name pool so re-running / reseeding always assigns the same
# name to the same barangay_id. "Jose Reyes" is pinned to Banaoang, Santa
# Barbara specifically to match the dashboard mockup already reviewed with
# the team; every other barangay draws from this pool in barangay_id order.
NAME_POOL = [
    "Ramon Bautista", "Cecilia Manalo", "Ferdinand Cruz", "Marilou Santos",
    "Edgardo Villanueva", "Rosalinda Aquino", "Danilo Mendoza", "Teresita Ramos",
    "Rogelio Domingo", "Corazon Fernandez", "Alberto Garcia", "Leonora Torres",
    "Rodrigo Castillo", "Imelda Navarro", "Bienvenido Pascual", "Nenita Ocampo",
    "Wilfredo Salazar", "Adelaida Gonzales", "Rustico Del Rosario", "Herminia Flores",
    "Renato Marquez", "Purificacion Ignacio", "Armando Velasco", "Esperanza Rivera",
    "Nestor Agustin", "Lourdes Panganiban", "Cirilo Bernardo", "Julieta Enriquez",
    "Bonifacio Lazaro", "Remedios Corpuz",
]

PINNED_NAMES = {
    # The dashboard mockup reviewed with the team labels this account
    # "Brgy. Banaoang, Sta. Barbara", but the only "Banaoang" among the 10
    # seeded target barangays per LGU is Calasiao's (barangay_id 23) — Santa
    # Barbara's own Banaoang exists in the GIS geojson but isn't one of the
    # 10 barangays this dataset uses. Pinned here to the one that's real.
    ("Banaoang", "Calasiao"): "Jose Reyes",
}

DESIGNATION = "Barangay Captain"


def _slug(text):
    return "".join(ch for ch in text.lower().replace(" ", "") if ch.isalnum())


LGU_SLUGS = {"Urdaneta City": "urdaneta", "Santa Barbara": "santabarbara", "Calasiao": "calasiao"}


def run():
    with app.app_context():
        barangays = Barangay.query.order_by(Barangay.barangay_id).all()
        existing_barangay_ids = {
            u.barangay_id for u in User.query.filter_by(role="barangay_user").all() if u.barangay_id
        }

        created = 0
        for i, b in enumerate(barangays):
            if b.barangay_id in existing_barangay_ids:
                continue

            name = PINNED_NAMES.get((b.barangay_name, b.city_municipality)) or NAME_POOL[i % len(NAME_POOL)]
            lgu_slug = LGU_SLUGS.get(b.city_municipality, _slug(b.city_municipality))
            email = f"{_slug(b.barangay_name)}.{lgu_slug}@reliefline.gov.ph"

            user = User(
                name=name,
                email=email,
                role="barangay_user",
                barangay_id=b.barangay_id,
                designation=DESIGNATION,
            )
            user.set_password(DEFAULT_PASSWORD)
            db.session.add(user)
            created += 1
            print(f"  {b.barangay_name} ({b.city_municipality}) -> {email}  [{name}]")

        db.session.commit()
        print(f"\nSeed complete. Created {created} barangay_user account(s); "
              f"{len(barangays) - created} barangay(s) already had one.")
        print(f"Shared dev password for all seeded barangay accounts: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    run()
