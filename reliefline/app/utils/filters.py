# Date filter helpers used on list pages.

from datetime import datetime


# Reads a date from a page filter in the address bar (e.g. ?date_from=2026-10-01).
# Returns nothing if the date is missing or not valid.
def arg_date(args, key):
    try:
        return datetime.strptime(args.get(key, ""), "%Y-%m-%d").date()
    except ValueError:
        return None


# Reads the 'from' and 'to' dates of a page's date filter.
def date_range(args, from_key="date_from", to_key="date_to"):
    return arg_date(args, from_key), arg_date(args, to_key)


# Checks if a date falls between the chosen 'from' and 'to' dates.
# If no dates are chosen, everything counts as in range.
def in_range(value, date_from, date_to):
    if not (date_from or date_to):
        return True
    if value is None:
        return False
    d = value.date() if isinstance(value, datetime) else value
    return (not date_from or d >= date_from) and (not date_to or d <= date_to)


# Turns a date into text like 2026-10-23 (blank if there is no date).
def iso(d):
    return d.isoformat() if d else ""
