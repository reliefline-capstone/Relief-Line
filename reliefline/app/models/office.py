from app.extensions import db

class Office(db.Model):
    __tablename__ = "offices"

    office_id = db.Column(db.Integer, primary_key=True)
    office_name = db.Column(db.String(100), nullable=False)
    office_type = db.Column(db.Enum("pswdo", "cswdo"), nullable=False)
    area_covered = db.Column(db.String(100), nullable=False)
    capacity_food_pack = db.Column(db.Integer, default=20000)

    # Warehouse "General Information" fields — optional since not every office
    # (e.g. plain CSWDO administrative offices) doubles as a staffed storage site.
    full_address = db.Column(db.String(255), nullable=True)
    manager_name = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))