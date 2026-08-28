"""
Trains the food-pack demand model: a Linear Regression that estimates how many
food packs a barangay needs from its profile.

Linear Regression is used per the ReliefLine capstone manuscript (Chapter 2 —
Predictive Model for Relief Goods): it produces interpretable, numerical
allocation outputs that LGU personnel can directly use for decision-making,
and it is practical for government settings where historical datasets may be
limited in size.

Trained on real AllocationRecord history — every allocation request logged
doubles as a labeled training example (features = the barangay's profile at
request time, label = predicted_quantity that was requested).

FEATURES is exactly the six predictor variables named in the manuscript's
Objective 1 and Model-phase description: population, poverty incidence,
disaster risk index, past calamity frequency, historical allocation, and
number of households. This list is the ONLY place the feature set is defined —
do not add a seventh predictor without a manuscript change.

--------------------------------------------------------------------------
Built to adapt when real data replaces the synthetic seed data
--------------------------------------------------------------------------
* `FEATURE_SOURCES` maps each predictor to the barangay attribute it reads.
  When a real per-barangay survey column replaces a synthetic one, point the
  mapping at the new attribute — the training loop, predict.py and the model
  version scheme are untouched.
* Missing values are expected on real government records. `_feature_value`
  returns `None` (not 0) for an absent field, and the pipeline's median
  `SimpleImputer` fills it at fit time — so a barangay with an incomplete
  profile still gets a prediction instead of a silently wrong 0.
  (`historical_allocation` is the one exception: a genuine 0 — "no prior
  allocation on record" — is real information, not a missing value.)
* `data_quality_report()` surfaces row count, per-feature missingness,
  each feature's correlation with the target, and a multicollinearity
  warning, so a data problem is visible before it quietly degrades accuracy.
* Leave-one-out cross-validation (per the manuscript) is kept for any dataset
  size — it is exact and cheap at the scale this system operates at.

Run scripts/train_model.py to (re)fit this against the current database.
"""
import os
from datetime import datetime

import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# The six manuscript predictors, in model-input order.
FEATURES = [
    "population",
    "poverty_incidence",
    "disaster_risk_index",
    "past_calamity_freq",
    "historical_allocation",
    "num_households",
]

# Which barangay attribute each predictor is read from. Swap a value here when
# a real data source replaces a synthetic one — nothing else needs to change.
# "historical_allocation" is derived (see historical_allocation_for), not a
# column, so it has no entry.
FEATURE_SOURCES = {
    "population": "population",
    "poverty_incidence": "poverty_incidence",
    "disaster_risk_index": "disaster_risk_index",
    "past_calamity_freq": "past_calamity_freq",
    "num_households": "num_households",
}

MODEL_VERSION = "v5.0-linreg-6f"
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


def _to_number(value):
    """Coerce a DB value to float, or None when it's genuinely absent. Real
    records may store numbers as strings ('1,240') or leave cells blank."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _feature_value(barangay, feature, as_of_date=None):
    """Single dispatch point for turning a barangay profile into one model
    input. Returns None for an absent field so the pipeline imputer can fill
    it (see module docstring). `historical_allocation` returns a real 0 when
    there is no prior record — that is information, not a gap."""
    if feature == "historical_allocation":
        return float(historical_allocation_for(barangay.barangay_id, before_date=as_of_date))
    source_attr = FEATURE_SOURCES.get(feature)
    if source_attr is None:
        raise ValueError(f"Unknown feature: {feature}")
    return _to_number(getattr(barangay, source_attr, None))


def feature_row(barangay, as_of_date=None):
    """One model input row, in FEATURES order. as_of_date, when given, caps
    historical_allocation to records strictly before that date — used only
    while building training rows (see _load_training_rows) so a barangay's
    own label never leaks into its own history feature."""
    return [[_feature_value(barangay, f, as_of_date) for f in FEATURES]]


def _load_training_rows():
    """Labeled examples = *realized* allocations (approved or released). A
    pending/rejected request never became an allocation, so it isn't history
    yet. Collapsed to one row per (barangay, event) — the same barangay can
    accumulate several draft/duplicate request rows for one event, and those
    would over-weight it — keeping the largest approved quantity."""
    from app.models.allocation import AllocationRecord

    rows = AllocationRecord.query.filter(
        AllocationRecord.status.in_(("approved", "released"))
    ).all()

    best = {}
    for a in rows:
        if a.barangay is None:
            continue
        key = (a.barangay_id, a.event_id) if a.event_id else ("solo", a.allocation_id)
        label = a.predicted_quantity or a.allocated_quantity or 0
        if key not in best or label > best[key][1]:
            best[key] = (a, label)

    X, y = [], []
    for a, label in best.values():
        X.append(feature_row(a.barangay, as_of_date=a.allocation_date)[0])
        y.append(label)
    return np.array(X, dtype=float), np.array(y, dtype=float)


def build_pipeline():
    """Median-impute -> standardize -> Linear Regression.

    The imputer is what lets an incomplete real-world barangay profile still
    produce a prediction; keep_empty_features handles the edge case where a
    whole predictor column is missing from a freshly-loaded dataset."""
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("linreg", LinearRegression()),
    ])


def _safe_mape(y, preds):
    """MAPE over the rows where the actual is non-zero — a zero actual makes
    the percentage undefined, and a relief allocation is never legitimately 0."""
    mask = y != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y[mask] - preds[mask]) / y[mask])) * 100)


def evaluate_loocv(X, y):
    """Leave-one-out CV — each fold refits build_pipeline() from scratch so the
    held-out point never influences its own prediction. Returns pooled
    out-of-fold predictions plus MAE/RMSE/MAPE/R² over that pooled set
    (per-fold R² is undefined with a single test point)."""
    loo = LeaveOneOut()
    preds = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in loo.split(X):
        pipe = build_pipeline()
        pipe.fit(X[train_idx], y[train_idx])
        preds[test_idx] = pipe.predict(X[test_idx])

    # A relief allocation is never negative — clamp, same as app.ml.predict.
    preds = np.clip(preds, 0, None)

    return {
        "mae": float(mean_absolute_error(y, preds)),
        "rmse": float(mean_squared_error(y, preds) ** 0.5),
        "mape": _safe_mape(y, preds),
        "r2": float(r2_score(y, preds)),
        "predictions": preds,
        "actual": y,
    }


def data_quality_report(X, y):
    """Human-readable checks that matter more once real data lands: how many
    rows, how complete each predictor is, how strongly each predictor moves
    with the target, and whether two predictors are near-duplicates (which
    makes individual coefficients unstable even though the fit still works)."""
    n = len(y)
    report = {"rows": n, "features": {}, "collinearity_warnings": []}

    for i, name in enumerate(FEATURES):
        col = X[:, i]
        missing = int(np.isnan(col).sum())
        present = col[~np.isnan(col)]
        if len(present) > 1 and np.std(present) > 0 and np.std(y) > 0:
            # Correlation on the rows where this feature is present.
            paired_y = y[~np.isnan(col)]
            corr = float(np.corrcoef(present, paired_y)[0, 1])
        else:
            corr = float("nan")
        report["features"][name] = {
            "missing": missing,
            "missing_pct": round(100 * missing / n, 1) if n else 0.0,
            "corr_with_target": round(corr, 3) if corr == corr else None,
        }

    # Pairwise near-collinearity (|r| >= 0.95) on complete rows.
    complete = ~np.isnan(X).any(axis=1)
    if complete.sum() > 2:
        Xc = X[complete]
        for i in range(len(FEATURES)):
            for j in range(i + 1, len(FEATURES)):
                a, b = Xc[:, i], Xc[:, j]
                if np.std(a) > 0 and np.std(b) > 0:
                    r = float(np.corrcoef(a, b)[0, 1])
                    if abs(r) >= 0.95:
                        report["collinearity_warnings"].append(
                            f"{FEATURES[i]} ~ {FEATURES[j]} (r={r:.2f}) — coefficients "
                            f"for these two will be unstable until they carry independent signal"
                        )
    return report


def train_and_persist():
    """Fits the final model on ALL allocation history, records honest
    leave-one-out metrics to ModelMetrics, and saves the fitted pipeline to
    disk for app.ml.predict to load. Returns metrics + the data-quality report."""
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    X, y = _load_training_rows()
    if len(y) < MIN_TRAINING_SAMPLES:
        raise RuntimeError(
            f"Only {len(y)} labeled allocation records found — need at least "
            f"{MIN_TRAINING_SAMPLES} to train a model that isn't pure noise."
        )

    quality = data_quality_report(X, y)
    metrics = evaluate_loocv(X, y)

    final_pipeline = build_pipeline()
    final_pipeline.fit(X, y)

    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    joblib.dump({
        "pipeline": final_pipeline,
        "features": FEATURES,
        "feature_sources": FEATURE_SOURCES,
        "version": MODEL_VERSION,
        "trained_at": datetime.utcnow().isoformat(),
        "training_rows": len(y),
    }, ARTIFACT_PATH)

    db.session.add(ModelMetrics(
        model_version=MODEL_VERSION,
        mae=round(metrics["mae"], 4),
        rmse=round(metrics["rmse"], 4),
        mape=round(metrics["mape"], 4) if metrics["mape"] == metrics["mape"] else None,
        r_squared=round(metrics["r2"], 4),
        training_samples=len(y),
    ))
    db.session.commit()

    metrics["quality"] = quality
    return metrics
