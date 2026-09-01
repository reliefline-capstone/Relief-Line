"""The whole system runs on Philippine time (Asia/Manila, UTC+8, no DST).

Every stored datetime is Philippine wall-clock time:
  * Python writes go through `ph_now()` / `ph_today()`
  * MySQL CURRENT_TIMESTAMP / NOW() server defaults are pinned to UTC+8 by
    SQLALCHEMY_ENGINE_OPTIONS (see app/config.py)

`ph_now` / `ph_today` are Jinja globals and `ph_time` is a Jinja filter for
formatting a stored datetime — all registered in app/__init__.py.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

PH_TZ = ZoneInfo("Asia/Manila")

DEFAULT_FORMAT = "%b %d, %Y %I:%M %p"


def ph_now():
    """Current Philippine wall-clock time as a naive datetime — correct no
    matter what time zone the host machine is set to."""
    return datetime.now(PH_TZ).replace(tzinfo=None)


def ph_today():
    """Today's date in Philippine time."""
    return ph_now().date()


def ph_time(dt, fmt=DEFAULT_FORMAT):
    """Format a stored datetime (already Philippine time) for display. Any
    tz-aware value is normalised to Philippine time first."""
    if dt is None:
        return ""
    if dt.tzinfo is not None:
        dt = dt.astimezone(PH_TZ).replace(tzinfo=None)
    return dt.strftime(fmt)
