# Database table: system settings.

from app.extensions import db


# Database table 'system_settings': settings the System Admin can change
# (e.g. warehouse 'Healthy'/'Moderate' stock levels, low-stock alerts).
class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    setting_key = db.Column(db.String(50), primary_key=True)
    setting_value = db.Column(db.String(255), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), onupdate=db.func.now())

    updated_by_user = db.relationship("User")
