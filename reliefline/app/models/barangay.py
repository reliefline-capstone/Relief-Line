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
    # Flood hazard descriptors used to split an LGU-level forecast across its
    # barangays (app.ml.predict). flood_susceptibility follows the MGB-style
    # 1 (low) - 4 (very high) classes. Values are synthetic until an official
    # MGB/NOAH layer is loaded - hazard_source says which it is.
    flood_susceptibility = db.Column(db.SmallInteger, default=2)
    river_proximity_km = db.Column(db.Numeric(5, 2), nullable=True)
    elevation_m = db.Column(db.Numeric(6, 1), nullable=True)
    hazard_source = db.Column(db.String(20), default="synthetic")