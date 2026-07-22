"""All datetimes are stored in UTC (datetime.utcnow()) — the standard,
timezone-safe way to store timestamps. This converts to Philippine time
(Asia/Manila, UTC+8, no DST) only at display time, via the `ph_time` Jinja
filter registered in app/__init__.py.
"""
from zoneinfo import ZoneInfo

PH_TZ = ZoneInfo("Asia/Manila")
_UTC = ZoneInfo("UTC")

DEFAULT_FORMAT = "%b %d, %Y %I:%M %p"


def to_ph_time(dt):
    """Naive UTC datetime -> timezone-aware Philippine-time datetime."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_UTC)
    return dt.astimezone(PH_TZ)


def ph_time(dt, fmt=DEFAULT_FORMAT):
    converted = to_ph_time(dt)
    return converted.strftime(fmt) if converted else ""
