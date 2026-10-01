"""Small helpers shared by the list pages' filter panels (_filter_panel.html)."""
from datetime import datetime


def arg_date(args, key):
    """A YYYY-MM-DD query-string value as a date, or None if missing/invalid."""
    try:
        return datetime.strptime(args.get(key, ""), "%Y-%m-%d").date()
    except ValueError:
        return None


def date_range(args, from_key="date_from", to_key="date_to"):
    """(date_from, date_to) from the query string - either may be None."""
    return arg_date(args, from_key), arg_date(args, to_key)


def in_range(value, date_from, date_to):
    """True when `value` (a date or datetime) falls inside the optional range.
    A missing value only passes when no range is set."""
    if not (date_from or date_to):
        return True
    if value is None:
        return False
    d = value.date() if isinstance(value, datetime) else value
    return (not date_from or d >= date_from) and (not date_to or d <= date_to)


def iso(d):
    return d.isoformat() if d else ""
