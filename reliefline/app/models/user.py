# Database table: user accounts.

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

# Database table 'users': user accounts - name, email, role, office or barangay,
# scrambled password, and whether the account is active.
class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("system_admin", "pswdo_admin", "cswdo_admin", "barangay_user"),
        nullable=False
    )
    office_id = db.Column(db.Integer, db.ForeignKey("offices.office_id"), nullable=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))
    must_change_password = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))
    last_login = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    office = db.relationship("Office")
    barangay = db.relationship("Barangay")

    # Gives the user's ID to the login system.
    def get_id(self):
        return str(self.user_id)


    # Saves a new password. It is stored scrambled (hashed), never as plain text,
    # so even someone reading the database can't see it.
    def set_password(self, raw_password):
        # The password is scrambled (hashed) before saving - the real password is never stored.
        self.password = generate_password_hash(raw_password)

    # Checks if the typed password matches the saved (scrambled) password.
    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
