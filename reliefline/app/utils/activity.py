"""Shared metadata + logging helper for admin-authored ActivityLog rows
(System Administration actions — user/office/barangay management, auth,
settings). Operational rows written elsewhere (allocation, distribution,
warehouse — see app.routes.pswdo/cswdo) are untouched and simply fall back
to DEFAULT_MODULE_LABEL.
"""
from datetime import datetime

from flask import request
from app.extensions import db
from app.models.activity_log import ActivityLog

MODULE_LABELS = {
    "login": "Authentication",
    "allocation_approved": "Allocation",
    "allocation_rejected": "Allocation",
    "relief_request_submitted": "Allocation",
    "distribution_status": "Distribution",
    "distribution_delivered": "Distribution",
    "warehouse_transfer_completed": "Inventory",
    "user_created": "User Management",
    "user_updated": "User Management",
    "user_activated": "User Management",
    "user_deactivated": "User Management",
    "user_password_reset": "User Management",
    "office_created": "Office Management",
    "office_updated": "Office Management",
    "office_activated": "Office Management",
    "office_deactivated": "Office Management",
    "barangay_created": "Barangay Management",
    "barangay_updated": "Barangay Management",
    "settings_updated": "System Settings",
}
DEFAULT_MODULE_LABEL = "Other"


def module_for_action(action_type):
    return MODULE_LABELS.get(action_type, DEFAULT_MODULE_LABEL)


# CSS class suffix (see static/css/admin.css .badge-module.mod-*) each module
# renders with — reuses the same color language as the rest of the app
# (blue/purple/amber/green/red/gray) rather than inventing a new palette.
MODULE_BADGE_CLASS = {
    "Authentication": "mod-blue",
    "Allocation": "mod-purple",
    "Distribution": "mod-amber",
    "Inventory": "mod-green",
    "User Management": "mod-red",
    "Office Management": "mod-blue",
    "Barangay Management": "mod-green",
    "System Settings": "mod-gray",
}
DEFAULT_MODULE_BADGE_CLASS = "mod-gray"


def module_badge_class(action_type):
    return MODULE_BADGE_CLASS.get(module_for_action(action_type), DEFAULT_MODULE_BADGE_CLASS)


def log_admin_activity(actor_id, action_type, description, office_id=None, barangay_id=None):
    """Writes an ActivityLog row for a System Administration action.

    is_read=True on purpose: these rows are visible on the admin's own
    System Activity page (which doesn't filter by is_read), but shouldn't
    inflate the PSWDO/CSWDO notification bell — that feed is for
    operational items awaiting their review, not admin housekeeping.
    """
    log = ActivityLog(
        actor_id=actor_id, action_type=action_type, description=description,
        office_id=office_id, barangay_id=barangay_id,
        ip_address=request.remote_addr if request else None,
        is_read=True, created_at=datetime.utcnow(),
    )
    db.session.add(log)
    return log
