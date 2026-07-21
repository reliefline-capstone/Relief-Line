"""
Trains the food-pack demand model: a Linear Regression that estimates how many
food packs a barangay needs from its profile.

Linear Regression is used per the ReliefLine capstone manuscript (Chapter 2 —
Predictive Model for Relief Goods): it produces interpretable, numerical
allocation outputs that LGU personnel can directly use for decision-making,
and it is practical for government settings where historical datasets may be
limited in size.

Trained on real AllocationRecord history — every allocation request PSWDO has
ever logged doubles as a labeled training example (features = the barangay's
profile at request time, label = predicted_quantity that was requested).

FEATURES is exactly the six predictor variables named in the manuscript's
Objective 1 and Model-phase description: population, poverty incidence,
disaster risk index, past calamity frequency, historical allocation, and
number of households.

The current dataset is synthetic seed data (real PSWDO/CSWDO figures haven't
arrived yet), which limits two of the six today:
  - num_households is a fixed population / 5 ratio in every seeded barangay
    right now, so it's perfectly collinear with population in this dataset.
    LinearRegression still fits without error (the least-squares solver just
    can't uniquely separate two identical columns), and it will separate
    normally once real household-count data — which won't follow a fixed
    ratio — replaces the seed values.
  - historical_allocation is computed dynamically per barangay (see
    historical_allocation_for) from whatever AllocationRecord history
    actually exists for it as of each row's date — 0 for a barangay's
    first-ever recorded request, a real prior figure once a second event's
    worth of history exists for it, same as it will behave on real data.

_feature_value()'s per-feature dispatch (rather than a hardcoded positional
list) is what keeps this "minimal changes" when real data replaces synthetic
data: swapping one predictor's data source only touches its branch below —
never the training loop, predict.py, or the model version scheme.

Leave-one-out cross-validation (not a train/test split) is used to estimate
real-world error, per the manuscript — with a still-small dataset, holding
out a fixed test slice would be statistically meaningless, and LOOCV uses
every row as a test point exactly once.

Run scripts/train_model.py to (re)fit this against the current database.
"""
import os
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = [
    "population",
    "poverty_incidence",
    "disaster_risk_index",
    "past_calamity_freq",
    "historical_allocation",
    "num_households",
]
MODEL_VERSION = "v4.0-linreg-6f"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")
MIN_TRAINING_SAMPLES = 5


def historical_allocation_for(barangay_id, before_date=None):
    """Manuscript's 'Historical Allocation' predictor: the most recent prior
    food-pack allocation on record for this barangay, from an earlier
    disaster event. 0 for a barangay's first-ever recorded request.

    before_date excludes records on/after that date so a training row can
    never "see" its own label (or a same-day duplicate) as its own history.
    Left as None at prediction time, where there's no later record to worry
    about excluding.
    """
    from app.models.allocation import AllocationRecord

    q = AllocationRecord.query.filter(AllocationRecord.barangay_id == barangay_id)
    if before_date is not None:
        q = q.filter(AllocationRecord.allocation_date < before_date)
    prior = q.order_by(AllocationRecord.allocation_date.desc()).first()
    return (prior.predicted_quantity or 0) if prior else 0


def _feature_value(barangay, feature, as_of_date=None):
    """Single dispatch point for turning a barangay profile into one model
    input. Swapping a predictor's data source later (e.g. a real per-barangay
    survey field instead of a synthetic seed column) means editing one branch
    here — nothing in the training loop or predict.py needs to change."""
    if feature == "population":
        return barangay.population or 0
    if feature == "num_households":
        return barangay.num_households or 0
    if feature == "poverty_incidence":
        return float(barangay.poverty_incidence or 0)
    if feature == "disaster_risk_index":
        return float(barangay.disaster_risk_index or 0)
    if feature == "past_calamity_freq":
        return barangay.past_calamity_freq or 0
    if feature == "historical_allocation":
        return historical_allocation_for(barangay.barangay_id, before_date=as_of_date)
    raise ValueError(f"Unknown feature: {feature}")


def feature_row(barangay, as_of_date=None):
    """One model input row, in FEATURES order. as_of_date, when given, caps
    historical_allocation to records strictly before that date — used only
    while building training rows (see _load_training_rows) so a barangay's
    own label never leaks into its own history feature."""
    return [[_feature_value(barangay, f, as_of_date) for f in FEATURES]]


def _load_training_rows():
    from app.models.allocation import AllocationRecord
    from app.models.barangay import Barangay

    rows = AllocationRecord.query.join(Barangay).all()
    X, y = [], []
    for a in rows:
        X.append(feature_row(a.barangay, as_of_date=a.allocation_date)[0])
        y.append(a.predicted_quantity or 0)
    return np.array(X, dtype=float), np.array(y, dtype=float)


def build_pipeline():
    return Pipeline([
        ("scale", StandardScaler()),
        ("linreg", LinearRegression()),
    ])


def evaluate_loocv(X, y):
    """Outer leave-one-out CV — with a still-small dataset this is the only
    sound way to estimate out-of-sample error. Each outer fold refits
    build_pipeline() from scratch, so the held-out point never influences its
    own prediction. Returns pooled out-of-fold
    predictions plus MAE/RMSE/MAPE/R² computed over that pooled set
    (per-fold R² is undefined with a single test point, so it must be
    computed on the pooled array)."""
    loo = LeaveOneOut()
    preds = np.zeros_like(y)
    for train_idx, test_idx in loo.split(X):
        pipe = build_pipeline()
        pipe.fit(X[train_idx], y[train_idx])
        preds[test_idx] = pipe.predict(X[test_idx])

    mae = float(mean_absolute_error(y, preds))
    rmse = float(mean_squared_error(y, preds) ** 0.5)
    mape = float(np.mean(np.abs((y - preds) / y)) * 100)
    r2 = float(r2_score(y, preds))
    return {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2, "predictions": preds, "actual": y}


def train_and_persist():
    """Fits the final model on ALL real allocation history, records honest
    leave-one-out metrics to ModelMetrics, and saves the fitted pipeline to
    disk for app.ml.predict to load."""
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    X, y = _load_training_rows()
    if len(y) < MIN_TRAINING_SAMPLES:
        raise RuntimeError(
            f"Only {len(y)} labeled allocation records found — need at least "
            f"{MIN_TRAINING_SAMPLES} to train a model that isn't pure noise."
        )

    metrics = evaluate_loocv(X, y)

    final_pipeline = build_pipeline()
    final_pipeline.fit(X, y)

    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    joblib.dump({"pipeline": final_pipeline, "features": FEATURES, "version": MODEL_VERSION}, ARTIFACT_PATH)

    db.session.add(ModelMetrics(
        model_version=MODEL_VERSION,
        mae=round(metrics["mae"], 4),
        rmse=round(metrics["rmse"], 4),
        mape=round(metrics["mape"], 4),
        r_squared=round(metrics["r2"], 4),
        training_samples=len(y),
    ))
    db.session.commit()
    return metrics
