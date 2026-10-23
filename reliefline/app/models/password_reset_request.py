# Database table: 'forgot password' requests, and the default reset password.

from app.extensions import db

DEFAULT_RESET_PASSWORD = "reliefline123"


# Database table 'password_reset_requests': 'forgot password' requests
# waiting for the System Admin to approve or deny.
class PasswordResetRequest(db.Model):
    __tablename__ = "password_reset_requests"

    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status = db.Column(db.Enum("pending", "approved", "denied"), nullable=False, default="pending")
    requested_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    is_seen = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))

    user = db.relationship("User", foreign_keys=[user_id])
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by])
