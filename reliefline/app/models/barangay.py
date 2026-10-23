# Database table: barangays.

from app.extensions import db

# Database table 'barangays': every barangay in the 3 target municipalities,
# with its population and number of households (families).
class Barangay(db.Model):
    __tablename__ = "barangays"

    barangay_id = db.Column(db.Integer, primary_key=True)
    barangay_name = db.Column(db.String(100), nullable=False)
    city_municipality = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer, default=0)
    num_households = db.Column(db.Integer, default=0)
