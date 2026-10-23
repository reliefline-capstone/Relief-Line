# Philippine date and time helpers (the whole app uses PH time).

from datetime import datetime
from zoneinfo import ZoneInfo

PH_TZ = ZoneInfo("Asia/Manila")

DEFAULT_FORMAT = "%b %d, %Y %I:%M %p"


# The current date and time in the Philippines.
# The whole app uses Philippine time, no matter where the server is.
def ph_now():
    return datetime.now(PH_TZ).replace(tzinfo=None)


# Today's date in the Philippines.
def ph_today():
    return ph_now().date()


# Formats a date/time for display in Philippine time (e.g. 'Oct 23, 2026 09:15 AM').
def ph_time(dt, fmt=DEFAULT_FORMAT):
    if dt is None:
        return ""
    if dt.tzinfo is not None:
        dt = dt.astimezone(PH_TZ).replace(tzinfo=None)
    return dt.strftime(fmt)
