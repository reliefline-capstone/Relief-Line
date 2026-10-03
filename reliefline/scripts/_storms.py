"""
Storm names -> typhoon_calendar keys, read straight from a relief report's
"Name of Typhoon" column. The relief reports are the ONLY basis for the
typhoon calendar (2026-10-03, on request - the earlier researched 36-storm
list was removed): a report naming "Luis & Maymay & Neneng & Pilandok" links
to luis_2026, maymay_2026, neneng_2026 and pilandok_2026, and each of those
becomes a calendar storm (see scripts/typhoon_calendar_from_reports.py).

"Habagat" (the southwest monsoon) is not a named storm and is dropped.
"""
import re

_NOT_A_STORM = {"habagat"}


def storm_names(name_field):
    """'Luis, Maymay, Neneng, Pilandok ' / 'Nika + Ofel + Pepito' /
    'Crising & Emong' -> ['Luis', 'Maymay', ...] (title case, Habagat dropped)."""
    parts = [p.strip() for p in re.split(r"[&,+]", name_field)]
    return [p.title() for p in parts if p and p.lower() not in _NOT_A_STORM]


def storm_keys(name_field, year):
    """typhoon_calendar keys for one report, e.g. ['maymay_2026', ...]."""
    return [f"{n.lower()}_{year}" for n in storm_names(name_field)]


def date_range(raw):
    """A report's "Date ng Typhoon" -> (start, end) as ISO strings. Handles
    '2025-07-22 to 2025-08-01', '22/07/2025 - 25/07/2025' (DD/MM/YYYY) and a
    single date in either format; end == start for a single date."""
    from datetime import datetime

    def one(s):
        s = s.strip()
        fmt = "%d/%m/%Y" if "/" in s else "%Y-%m-%d"
        return datetime.strptime(s, fmt).date().isoformat()

    parts = re.split(r"\s+to\s+|\s+-\s+", raw.strip())
    return one(parts[0]), one(parts[-1])
