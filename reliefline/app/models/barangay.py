from app.extensions import db

class Barangay(db.Model):
    __tablename__ = "barangays"

    barangay_id = db.Column(db.Integer, primary_key=True)
    barangay_name = db.Column(db.String(100), nullable=False)
    city_municipality = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer, default=0)
    num_households = db.Column(db.Integer, default=0)
    poverty_incidence = db.Column(db.Numeric(5, 2), default=0)
    disaster_risk_index = db.Column(db.Numeric(4, 2), default=0)
    past_calamity_freq = db.Column(db.Integer, default=0)