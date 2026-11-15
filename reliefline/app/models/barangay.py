# Database table: barangays.

import math

from app.extensions import db

# Food packs set aside per family in the 'other disasters' reserve (fire, earthquake, etc.).
RESERVE_PACKS_PER_FAMILY = 1
# Reserve % given to a barangay until the System Admin changes it.
DEFAULT_RESERVE_PCT = 1.0


# Database table 'barangays': every barangay in the 3 target municipalities,
# with its population, number of households (families) and its 'other disasters' reserve %.
class Barangay(db.Model):
    __tablename__ = "barangays"

    barangay_id = db.Column(db.Integer, primary_key=True)
    barangay_name = db.Column(db.String(100), nullable=False)
    city_municipality = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer, default=0)
    num_households = db.Column("total_families", db.Integer, default=0)
    # % of the barangay's families to keep food packs for, for disasters the typhoon model can't predict.
    reserve_pct = db.Column(db.Numeric(5, 2), nullable=False, default=DEFAULT_RESERVE_PCT)

    # Packs to keep on hand all year for other disasters: reserve % x families x packs per family (rounded up).
    @property
    def reserve_packs(self):
        pct = float(self.reserve_pct or 0)
        return math.ceil(pct / 100 * (self.num_households or 0) * RESERVE_PACKS_PER_FAMILY - 1e-9)


# Total 'other disasters' reserve for a municipality: the sum of its barangays' reserves.
def lgu_reserve_packs(lgu):
    return sum(b.reserve_packs for b in Barangay.query.filter_by(city_municipality=lgu).all())
