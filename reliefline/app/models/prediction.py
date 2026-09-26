from app.extensions import db

class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    barangay_id = db.Column(db.Integer, db.ForeignKey("barangays.barangay_id"), nullable=False)
    predicted_quantity = db.Column(db.Integer, nullable=False)
    input_snapshot = db.Column(db.Text, nullable=False)
    predicted_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    model_version = db.Column(db.String(50), default="v1.0")


class ModelMetrics(db.Model):
    __tablename__ = "model_metrics"

    metric_id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(50), default="v1.0")
    mae = db.Column(db.Numeric(10, 4), nullable=True)
    rmse = db.Column(db.Numeric(10, 4), nullable=True)
    mape = db.Column(db.Numeric(10, 4), nullable=True)
    r_squared = db.Column(db.Numeric(10, 4), nullable=True)
    training_samples = db.Column(db.Integer, nullable=True)
    # Rolling-origin backtest extras (SARIMAX forecaster): WAPE, the share of
    # backtest months where actual demand stayed at/below the P90 safety stock
    # (should be ~0.90), and the same WAPE for the seasonal-naive benchmark.
    wape = db.Column(db.Numeric(10, 4), nullable=True)
    p90_coverage = db.Column(db.Numeric(6, 4), nullable=True)
    naive_wape = db.Column(db.Numeric(10, 4), nullable=True)
    # Error of the 12-month total (what a stockpile decision uses), model vs
    # the seasonal-naive benchmark. 0.23 = the 12-month total is off by ~23%.
    total12_err = db.Column(db.Numeric(10, 4), nullable=True)
    naive_total12_err = db.Column(db.Numeric(10, 4), nullable=True)
    trained_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))