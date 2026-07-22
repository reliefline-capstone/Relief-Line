from app.extensions import db


class SystemSetting(db.Model):
    """Simple key/value store for admin-editable operational settings (e.g.
    warehouse stock thresholds). Deliberately schemaless beyond key/value so
    new settings can be introduced from app.utils.settings without a
    migration — see get_setting()/set_setting() for typed access."""

    __tablename__ = "system_settings"

    setting_key = db.Column(db.String(50), primary_key=True)
    setting_value = db.Column(db.String(255), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"), onupdate=db.func.now())

    updated_by_user = db.relationship("User")
