from app.extensions import db

# "Event Category" choices on the Declare Disaster Event form (PSWDO and
# CSWDO/MSWDO) - PAGASA's tropical cyclone categories plus the hazards that
# come with them. Several can be picked; they're stored comma-joined in
# DisasterEvent.weather_condition (e.g. "Typhoon, Flood").
EVENT_CATEGORIES = [
    "Tropical Depression",
    "Tropical Storm",
    "Severe Tropical Storm",
    "Typhoon",
    "Super Typhoon",
    "Southwest Monsoon (Habagat)",
    "Flood",
    "Storm Surge",
    "Landslide",
]


def event_categories_from_form(form):
    """The ticked Event Category checkboxes, in list order, comma-joined -
    or None when none are ticked. Unknown values are dropped."""
    picked = set(form.getlist("event_category"))
    chosen = [c for c in EVENT_CATEGORIES if c in picked]
    return ", ".join(chosen) or None


class DisasterEvent(db.Model):
    __tablename__ = "disaster_events"

    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(150), nullable=False)
    event_type = db.Column(db.Enum("typhoon", "flood", "other"), default="typhoon")
    status = db.Column(db.Enum("active", "monitoring", "ended"), default="active")
    # Shown as "Event Category"; comma-joined EVENT_CATEGORIES (see above).
    weather_condition = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    # "province" = PSWDO's traditional system-wide declare (city_municipality
    # stays None, applies to every barangay - unchanged legacy behavior).
    # "municipality" = a CSWDO's own local declare, scoped to their own town
    # and (via EventBarangay) an explicit subset of its barangays.
    scope = db.Column(db.Enum("province", "municipality"), nullable=False,
                       default="province", server_default="province")
    city_municipality = db.Column(db.String(100), nullable=True)

    # True only for the 36 historical-calendar rows seeded by
    # scripts/typhoon_calendar_2021_2026.py (status='ended', scope='province')
    # - kept out of every staff-facing event picker (see the is_reference=False
    # filters in cswdo.py/reports.py/barangay.py/pswdo.py) so 2021-2026
    # calendar noise never shows up next to something a CSWDO/PSWDO admin
    # actually declared.
    is_reference = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))