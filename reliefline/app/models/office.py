from app.extensions import db

class Office(db.Model):
    __tablename__ = "offices"

    office_id = db.Column(db.Integer, primary_key=True)
    office_name = db.Column(db.String(100), nullable=False)
    office_type = db.Column(db.Enum("pswdo", "cswdo"), nullable=False)
    area_covered = db.Column(db.String(100), nullable=False)
    capacity_food_pack = db.Column(db.Integer, default=20000)