from app.extensions import db

# Shared with app.routes.admin's grant handler and app.routes.auth's forced
# password-change screen — same default used by scripts/seed_barangay_users.py
# for freshly-seeded barangay accounts, so there's one convention for "the
# ReliefLine default password" across the app.
DEFAULT_RESET_PASSWORD = "reliefline123"


class PasswordResetRequest(db.Model):
    """A user-initiated request (from the public "Forgot Password" page) to
    have their account password reset to DEFAULT_RESET_PASSWORD. Routed to a
    System Administrator for manual approval rather than resetting
    automatically or emailing a self-service link — see
    app.routes.admin.approve_password_reset_request / deny_password_reset_request.
    """
    __tablename__ = "password_reset_requests"

    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status = db.Column(db.Enum("pending", "approved", "denied"), nullable=False, default="pending")
    requested_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    # Drives the sidebar's red badge, separately from `status` — a request
    # stays "pending" (and listed under the Pending tab) until it's granted
    # or denied, but is_seen flips to True the moment a System Administrator
    # opens the Password Reset Requests page, so the badge only flags NEW
    # activity rather than every still-unresolved request.
    is_seen = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))

    user = db.relationship("User", foreign_keys=[user_id])
    reviewed_by_user = db.relationship("User", foreign_keys=[reviewed_by])
