# Database table: disaster events, and the list of event categories.

from app.extensions import db

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


# Reads the ticked event categories (Typhoon, Flood, Storm Surge...) from a form
# and joins them into one text, e.g. 'Typhoon, Flood'.
def event_categories_from_form(form):
    picked = set(form.getlist("event_category"))
    chosen = [c for c in EVENT_CATEGORIES if c in picked]
    return ", ".join(chosen) or None


# Database table 'disaster_events': disaster events (typhoons, floods) declared in the system.
# An event is province-wide or local to one municipality, and is active or ended.
class DisasterEvent(db.Model):
    __tablename__ = "disaster_events"

    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(150), nullable=False)
    event_type = db.Column(db.Enum("typhoon", "flood", "other"), default="typhoon")
    status = db.Column(db.Enum("active", "monitoring", "ended"), default="active")
    weather_condition = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)

    scope = db.Column(db.Enum("province", "municipality"), nullable=False,
                       default="province", server_default="province")
    city_municipality = db.Column(db.String(100), nullable=True)

    is_reference = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("0"))
