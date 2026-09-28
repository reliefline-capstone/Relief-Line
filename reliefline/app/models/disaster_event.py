from app.extensions import db

class DisasterEvent(db.Model):
    __tablename__ = "disaster_events"

    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(150), nullable=False)
    event_type = db.Column(db.Enum("typhoon", "flood", "other"), default="typhoon")
    status = db.Column(db.Enum("active", "monitoring", "ended"), default="active")
    weather_condition = db.Column(db.String(50), nullable=True)
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