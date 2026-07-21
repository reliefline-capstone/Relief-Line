"""
Loads the Linear Regression model trained by app.ml.train and predicts a
barangay's food-pack demand from its real profile fields — the same six
manuscript-specified predictors app.ml.train fits on (see FEATURES /
feature_row there): population, poverty incidence, disaster risk index, past
calamity frequency, historical allocation, and number of households.

Used by the Predictive Analytics page to estimate demand for barangays that
haven't had a formal relief request submitted yet — for barangays that
already have one, the real requested/approved/released figures (see
pswdo._relief_summary) are used instead, since an actual request is always
better evidence than a model estimate.
"""
import json
from datetime import date

import joblib

from app.ml.train import ARTIFACT_PATH, feature_row, historical_allocation_for

_cached_artifact = None
_load_attempted = False


def _load_artifact():
    global _cached_artifact, _load_attempted
    if not _load_attempted:
        _load_attempted = True
        try:
            _cached_artifact = joblib.load(ARTIFACT_PATH)
        except FileNotFoundError:
            _cached_artifact = None
    return _cached_artifact


def is_model_available():
    return _load_artifact() is not None


def predict_quantity(barangay):
    """Estimated food-pack demand for one barangay, or None if no model has
    been trained yet (see scripts/train_model.py)."""
    artifact = _load_artifact()
    if artifact is None:
        return None
    raw = artifact["pipeline"].predict(feature_row(barangay))[0]
    return max(int(round(raw)), 0)


def log_prediction_once_per_day(barangay, predicted_quantity):
    """Writes a real PredictionLog row (input snapshot + output), deduped per
    barangay per day so repeated page loads don't spam the table with
    identical rows."""
    from app.extensions import db
    from app.models.prediction import PredictionLog

    artifact = _load_artifact()
    if artifact is None:
        return None

    existing = PredictionLog.query.filter(
        PredictionLog.barangay_id == barangay.barangay_id,
        PredictionLog.model_version == artifact["version"],
        db.func.date(PredictionLog.predicted_at) == date.today(),
    ).first()
    if existing:
        return existing

    snapshot = {
        "population": barangay.population,
        "num_households": barangay.num_households,
        "poverty_incidence": float(barangay.poverty_incidence) if barangay.poverty_incidence is not None else None,
        "disaster_risk_index": float(barangay.disaster_risk_index) if barangay.disaster_risk_index is not None else None,
        "past_calamity_freq": barangay.past_calamity_freq,
        "historical_allocation": historical_allocation_for(barangay.barangay_id),
    }
    log = PredictionLog(
        barangay_id=barangay.barangay_id,
        predicted_quantity=predicted_quantity,
        input_snapshot=json.dumps(snapshot),
        model_version=artifact["version"],
    )
    db.session.add(log)
    db.session.commit()
    return log
