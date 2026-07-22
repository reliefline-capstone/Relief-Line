"""Typed accessors for app.models.system_setting.SystemSetting.

Settings are stored as plain strings; callers cast on read. A missing key
(nothing saved yet, or a fresh DB) silently falls back to `default` instead
of raising, so every call site works before the System Settings page has
ever been used.
"""
from app.extensions import db
from app.models.system_setting import SystemSetting

# key -> (default, cast, label) — the single place a new admin-editable
# setting gets registered. admin.settings_page() renders a field per entry.
SETTINGS_SCHEMA = {
    "warehouse_healthy_threshold": (0.70, float, "Healthy stock threshold (% of capacity)"),
    "warehouse_moderate_threshold": (0.30, float, "Moderate stock threshold (% of capacity)"),
    "low_stock_alert_enabled": (True, bool, "Send low-stock alerts"),
}


def get_setting(key, default=None, cast=str):
    row = SystemSetting.query.get(key)
    if row is None:
        return default
    if cast is bool:
        return row.setting_value.lower() in ("1", "true", "yes", "on")
    try:
        return cast(row.setting_value)
    except (TypeError, ValueError):
        return default


def set_setting(key, value, user_id=None):
    row = SystemSetting.query.get(key)
    str_value = "1" if value is True else "0" if value is False else str(value)
    if row is None:
        row = SystemSetting(setting_key=key, setting_value=str_value, updated_by=user_id)
        db.session.add(row)
    else:
        row.setting_value = str_value
        row.updated_by = user_id
