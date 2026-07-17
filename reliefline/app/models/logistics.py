from app.extensions import db

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    vehicle_id = db.Column(db.Integer, primary_key=True)
    vehicle_name = db.Column(db.String(100), nullable=False)
    plate_number = db.Column(db.String(20), nullable=True)
    capacity_packs = db.Column(db.Integer, nullable=True)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)

    office = db.relationship("Office", backref="vehicles")


class Driver(db.Model):
    __tablename__ = "drivers"

    driver_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)

    office = db.relationship("Office", backref="drivers")
