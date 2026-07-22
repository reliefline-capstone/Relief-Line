from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

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
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("1"))
    last_login = db.Column(db.DateTime, nullable=True)
    # Heartbeat updated on every authenticated request (see app.__init__'s
    # before_request hook) — distinct from last_login, which only moves at
    # sign-in. app.utils.presence.is_online() compares this against "now" to
    # decide whether someone is genuinely online right now, not just logged
    # in at some point today.
    last_activity = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    office = db.relationship("Office")
    barangay = db.relationship("Barangay")

    def get_id(self):
        return str(self.user_id)

    # flask_login.UserMixin.is_active is a settable property by default, but
    # our own `is_active` DB column shadows it automatically as an instance
    # attribute — no override needed, this comment just documents why.

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)