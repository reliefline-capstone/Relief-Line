from app.extensions import db


class ClimateMonthly(db.Model):
    """Province-wide monthly climate context for the forecaster's predictors.

    rainfall_normal_mm - PAGASA Dagupan 1991-2020 normal for that calendar
                         month (real).
    rainfall_mm        - the month's rainfall: the normal scaled up by the
                         severity of any event that month (synthetic).
    oni                - NOAA Oceanic Nino Index for the month (real).
    event_count / max_event_severity - storms that affected Pangasinan that
                         month, from app.ml.climate_reference.EVENTS.
    """
    __tablename__ = "climate_monthly"

    month_start = db.Column(db.Date, primary_key=True)
    rainfall_normal_mm = db.Column(db.Numeric(7, 1), nullable=False)
    rainfall_mm = db.Column(db.Numeric(7, 1), nullable=False)
    oni = db.Column(db.Numeric(3, 1), nullable=True)
    event_count = db.Column(db.SmallInteger, nullable=False, default=0)
    max_event_severity = db.Column(db.SmallInteger, nullable=False, default=0)
    data_source = db.Column(db.String(40), nullable=False, default="rain:synthetic;oni:noaa")
