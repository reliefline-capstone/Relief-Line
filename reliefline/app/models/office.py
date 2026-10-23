# Database table: PSWDO and CSWDO/MSWDO offices.

from app.extensions import db

# Database table 'offices': the PSWDO provincial office/depots and the CSWDO/MSWDO municipal offices,
# with their address, contact person and warehouse food pack capacity.
class Office(db.Model):
    __tablename__ = "offices"

    office_id = db.Column(db.Integer, primary_key=True)
    office_name = db.Column(db.String(100), nullable=False)
    office_type = db.Column(db.Enum("pswdo", "cswdo"), nullable=False)
    area_covered = db.Column(db.String(100), nullable=False)
    capacity_food_pack = db.Column(db.Integer, default=20000)

    full_address = db.Column(db.String(255), nullable=True)
    manager_name = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))
