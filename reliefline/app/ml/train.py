"""
Trains the food-pack demand model: a Ridge regression that estimates how many
food packs a barangay needs from its profile (population, poverty incidence,
disaster risk index, past calamity frequency).

Trained on real AllocationRecord history — every allocation request PSWDO has
ever logged doubles as a labeled training example (features = the barangay's
profile at request time, label = predicted_quantity that was requested).

Only ~11 barangays have a submitted allocation to learn from so far, which
shapes several choices below:
  - num_households is dropped as a feature: it equals population / 5 in every
    row (a fixed household-size assumption baked into the seed data), so it's
    perfectly collinear with population and adds no signal.
  - historical_allocation is dropped: it is 0 for every row so far (there has
    only ever been one disaster event on record), so it has zero variance to
    learn from. Wire it back in once repeat-event history exists.
  - Ridge, not plain LinearRegression, is used on purpose: 4 features over
    ~11 samples is a near-saturated fit, and L2 regularization keeps
    coefficients from swinging wildly to chase noise in such a small sample.
  - Leave-one-out cross-validation (not a train/test split) is used to
    estimate real-world error — holding out a fixed test slice from ~11 rows
    would be statistically meaningless either way, and LOOCV uses every row
    as a test point exactly once.

Run scripts/train_model.py to (re)fit this against the current database.
"""
import os
import numpy as np
import joblib
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = ["population", "poverty_incidence", "disaster_risk_index", "past_calamity_freq"]
MODEL_VERSION = "v2.0-ridgecv"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")
MIN_TRAINING_SAMPLES = 5

# Regularization strength is auto-tuned per fit (RidgeCV), not hand-picked —
# with only a handful of labeled barangays, the model itself decides, via its
# own inner cross-validation, how much to trust the features vs. fall back
# toward the historical average. Scored on MAE rather than R² because R² is
# undefined for the single-point folds a leave-one-out inner split produces.
ALPHA_GRID = np.logspace(-1, 4, 40)


def _load_training_rows():
    from app.models.allocation import AllocationRecord
    from app.models.barangay import Barangay

    rows = AllocationRecord.query.join(Barangay).all()
    X, y = [], []
    for a in rows:
        b = a.barangay
        X.append([
            b.population or 0,
            float(b.poverty_incidence or 0),
            float(b.disaster_risk_index or 0),
            b.past_calamity_freq or 0,
        ])
        y.append(a.predicted_quantity or 0)
    return np.array(X, dtype=float), np.array(y, dtype=float)


def build_pipeline():
    return Pipeline([
        ("scale", StandardScaler()),
        ("ridge", RidgeCV(alphas=ALPHA_GRID, cv=LeaveOneOut(), scoring="neg_mean_absolute_error")),
    ])


def evaluate_loocv(X, y):
    """Outer leave-one-out CV — with n≈11 this is the only sound way to
    estimate out-of-sample error. Each outer fold refits build_pipeline()
    from scratch (including its own inner CV for alpha), so the held-out
    point never influences its own prediction. Returns pooled out-of-fold
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
