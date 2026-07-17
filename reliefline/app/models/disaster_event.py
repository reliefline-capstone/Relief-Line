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