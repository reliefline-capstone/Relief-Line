# Activity log helpers (save an entry, section names, badge colors).

from app.utils.timezone import ph_now

from flask import request
from app.extensions import db
from app.models.activity_log import ActivityLog

MODULE_LABELS = {
    "login": "Authentication",
    "allocation_approved": "Allocation",
    "allocation_rejected": "Allocation",
    "relief_request_submitted": "Allocation",
    "direct_allocation": "Allocation",
    "cswdo_proactive_allocation": "Allocation",
    "disaster_event_declared": "Disaster Events",
    "disaster_event_ended": "Disaster Events",
    "distribution_status": "Distribution",
    "distribution_delivered": "Distribution",
    "warehouse_transfer_completed": "Inventory",
    "user_created": "User Management",
    "user_updated": "User Management",
    "user_activated": "User Management",
    "user_deactivated": "User Management",
    "user_password_reset": "User Management",
    "password_reset_request_approved": "User Management",
    "password_reset_request_denied": "User Management",
    "office_created": "Office Management",
    "office_updated": "Office Management",
    "office_activated": "Office Management",
    "office_deactivated": "Office Management",
    "barangay_created": "Barangay Management",
    "barangay_updated": "Barangay Management",
    "settings_updated": "System Settings",
}
DEFAULT_MODULE_LABEL = "Other"


# Tells which part of the system an activity belongs to (e.g. 'User Management', 'Authentication').
# Used to group and filter the System Activity log.
def module_for_action(action_type):
    return MODULE_LABELS.get(action_type, DEFAULT_MODULE_LABEL)


MODULE_BADGE_CLASS = {
    "Authentication": "mod-blue",
    "Allocation": "mod-purple",
    "Distribution": "mod-amber",
    "Inventory": "mod-green",
    "User Management": "mod-red",
    "Office Management": "mod-blue",
    "Barangay Management": "mod-green",
    "System Settings": "mod-gray",
    "Disaster Events": "mod-red",
}
DEFAULT_MODULE_BADGE_CLASS = "mod-gray"


# Picks the badge color shown next to an activity, based on its part of the system.
def module_badge_class(action_type):
    return MODULE_BADGE_CLASS.get(module_for_action(action_type), DEFAULT_MODULE_BADGE_CLASS)


# Saves one entry in the activity log: who did what, when, and from which computer (IP address).
# Used for System Admin actions like creating users or resetting passwords.
def log_admin_activity(actor_id, action_type, description, office_id=None, barangay_id=None):
    log = ActivityLog(
        actor_id=actor_id, action_type=action_type, description=description,
        office_id=office_id, barangay_id=barangay_id,
        ip_address=request.remote_addr if request else None,
        is_read=True, created_at=ph_now(),
    )
    db.session.add(log)
    return log
