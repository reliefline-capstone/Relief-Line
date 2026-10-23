# Loads all database tables when the app starts.

from app.models import (
    activity_log,
    allocation,
    barangay,
    barangay_inventory,
    barangay_report,
    barangay_status,
    disaster_event,
    event_barangay,
    family,
    food_pack_batch,
    logistics,
    office,
    password_reset_request,
    prediction,
    relief_request_batch,
    report,
    system_setting,
    user,
    validation,
    warehouse,
)
