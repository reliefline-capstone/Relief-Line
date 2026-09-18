"""
Trains the food-pack TIME-FORECASTING model: projects total food-pack demand
per LGU (Urdaneta City, Santa Barbara, Calasiao) over future calendar
months, so PSWDO/CSWDO can answer "how many food packs should we have in
stock for the next 4 / 6 / 12 months" - not just "how many does this one
barangay need for this one event," which is what the model answered before.

This REPLACES the earlier per-barangay/per-event point model (manuscript
Objective 1 revision - time forecasting, per the panel). Linear Regression
is kept as the estimator (per the ReliefLine capstone manuscript's original
justification: interpretable, numerical outputs LGU personnel can directly
use, practical for small government datasets) - what changed is the
predictor set and the unit of prediction, not the model family.

--------------------------------------------------------------------------
Why the predictors changed
--------------------------------------------------------------------------
The old six predictors (population, poverty_incidence, disaster_risk_index,
past_calamity_freq, historical_allocation, num_households) are almost all
STATIC per barangay - they explain "how big/vulnerable is this place," not
"why is demand higher in August than March." A forecasting model needs
predictors that carry a TIME dimension. FEATURES below is the new,
deliberate set:

  - month_sin / month_cos   - cyclical calendar position (Jun-Nov typhoon
                               season should surface as a smooth bump, not
                               a hard flag)
  - lag_1 / lag_3 / rolling_mean_3 - the LGU's own recent-history signal,
                               the standard autoregressive forecasting
                               feature, computed over the representative
                               annual cycle below
  - active_disaster_events  - how many trusted calibration events
                               historically landed in this LGU-month
  - population               - LGU scale (sum across its barangays)
  - disaster_risk_index      - LGU vulnerability (mean across its barangays)
  - historical_allocation    - THIS LGU's overall typical monthly scale
                               (mean of its 12 monthly totals) - a single
                               constant per LGU, distinct from the
                               month-specific lag features above

Dropped: poverty_incidence, num_households, past_calamity_freq as individual
predictors - weak temporal relevance at LGU-month granularity, and largely
redundant with disaster_risk_index/population once pooled to LGU level. This
is a deliberate, documented pruning, not a silent drop - re-run
data_quality_report() once real data lands to confirm empirically.

--------------------------------------------------------------------------
Why LGU-level, not per-barangay
--------------------------------------------------------------------------
Most individual barangays have only a handful of historical allocation
events each - nowhere near enough to fit a reliable time series per
barangay (87 independent, mostly-empty series). Pooling to the 3 LGUs gives
each series far more combined monthly data. app.ml.predict.forecast_barangay
still answers a per-barangay question, via a top-down proportional split of
the LGU forecast - see that module.

--------------------------------------------------------------------------
Why a "representative annual cycle," not a literal multi-year trend
--------------------------------------------------------------------------
The underlying history spans only a handful of distinct dates across
2023-2025 (one date per calibration event), not a dense, continuous monthly
series - there is no reliable way to separate "real year-over-year growth"
from "which barangays a given synthetic event happened to hit." So training
rows are built as one point per (LGU, calendar month 1-12), pooling
whichever years each event landed in - the model learns a typical seasonal
shape per LGU, not a trend across years. This is a stated limitation, not a
hidden one: revisit once several full years of dense real monthly records
exist (see CALIBRATION_EVENT_NAMES below on keeping the training set honest
as real data arrives).

--------------------------------------------------------------------------
Keeping the training set honest
--------------------------------------------------------------------------
CALIBRATION_EVENT_NAMES is a deliberate allow-list, not "every
AllocationRecord with status approved/released" - ad hoc events created
while exercising the app during development/testing (e.g. "Test Typhoon")
must never leak into training. Add a real historical event's name here once
real PSWDO/CSWDO records replace a synthetic one; nothing else in this
module needs to change.

Run scripts/train_model.py to (re)fit this against the current database.
Run scripts/seed_training_data.py + scripts/seed_seasonal_events.py first
if the database doesn't yet have calibration events covering every month.
"""
import math
import os

from app.utils.timezone import ph_now

import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Trusted historical events used to calibrate the model - see module
# docstring ("Keeping the training set honest"). The 6 typhoon-season events
# and 3 legacy events are scripts/seed_training_data.py's SYNTHETIC_EVENTS /
# LEGACY_EVENT_SEVERITY; the 6 off-season events are
# scripts/seed_seasonal_events.py's OFF_SEASON_EVENTS, added specifically so
# every calendar month has real training evidence.
CALIBRATION_EVENT_NAMES = {
    "Typhoon Egay (2023)", "Typhoon Kabayan (2023)", "Typhoon Carina (2024)",
    "Super Typhoon Julian (2024)", "Tropical Storm Dante (2025)", "Typhoon Ramil (2025)",
    "Typhoon Inday", "Tropical Storm Basyang", "Tropical Storm Ada",
    "Localized Flooding (Jan)", "Localized Flooding (Feb)", "Summer Heat Advisory (Mar)",
    "Localized Flashflood (Apr)", "Pre-Monsoon Squall (May)", "Amihan Tail-end Flooding (Dec)",
}

# The new time-forecasting predictors, in model-input order.
FEATURES = [
    "month_sin",
    "month_cos",
    "lag_1",
    "lag_3",
    "rolling_mean_3",
    "active_disaster_events",
    "population",
    "disaster_risk_index",
    "historical_allocation",
]

MODEL_VERSION = "v7.0-timefc-lgu"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")
MIN_TRAINING_SAMPLES = 5

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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


def _realized_quantity(alloc):
    """Food packs actually granted on one AllocationRecord - the
    approved/allocated amount, falling back to the requested amount only for
    older records saved before allocated_quantity was populated. A genuine 0
    is meaningful and kept."""
    if alloc.allocated_quantity:
        return alloc.allocated_quantity
    return alloc.predicted_quantity or 0


def historical_allocation_for(barangay_id, before_date=None):
    """One barangay's own historical allocation pattern - the median of its
    realized per-event allocations (records collapsed to one figure per
    event first, so a barangay with several rows for one typhoon isn't
    over-weighted). Kept from the earlier per-barangay model: still used by
    app.ml.predict for the per-barangay proportional split of the new
    LGU-level forecast (see forecast_barangay), since it's the right
    signal for "how much of this LGU's forecast should this specific
    barangay's share be."

    Only 'approved'/'released' records count - same filter the LGU-month
    aggregation applies. Returns 0 for a barangay with no realized
    allocation on record ("no prior allocation" is real information, not a
    missing value). before_date excludes records on/after that date so a
    row can never "see" its own label as its own history.
    """
    import statistics
    from app.models.allocation import AllocationRecord

    q = AllocationRecord.query.filter(
        AllocationRecord.barangay_id == barangay_id,
        AllocationRecord.status.in_(("approved", "released")),
    )
    if before_date is not None:
        q = q.filter(AllocationRecord.allocation_date < before_date)
    records = q.all()
    if not records:
        return 0

    per_event = {}
    for rec in records:
        key = rec.event_id if rec.event_id is not None else ("solo", rec.allocation_id)
        per_event[key] = max(per_event.get(key, 0), _realized_quantity(rec))

    return float(statistics.median(per_event.values()))


def _load_monthly_lgu_rows():
    """Pulls every trusted-calibration AllocationRecord (approved/released,
    event name in CALIBRATION_EVENT_NAMES), aggregates to one entry per
    (LGU, calendar month 1-12), pooling across whichever years each
    calibration event happened to land in.

    Returns {(lgu, month): {"total": int, "event_names": {str, ...}}}.
    """
    from app.models.allocation import AllocationRecord
    from app.models.disaster_event import DisasterEvent

    rows = AllocationRecord.query.join(
        DisasterEvent, AllocationRecord.event_id == DisasterEvent.event_id
    ).filter(
        AllocationRecord.status.in_(("approved", "released")),
        DisasterEvent.event_name.in_(CALIBRATION_EVENT_NAMES),
    ).all()

    table = {}
    for a in rows:
        b = a.barangay
        if b is None:
            continue
        key = (b.city_municipality, a.allocation_date.month)
        entry = table.setdefault(key, {"total": 0, "event_names": set()})
        entry["total"] += _realized_quantity(a)
        entry["event_names"].add(a.event.event_name)
    return table


def _lgu_scale_features(lgus, monthly_table):
    """LGU-level features that don't vary by month: population (summed
    across the LGU's barangays), disaster_risk_index (averaged), and
    historical_allocation (mean of the LGU's 12 monthly totals - this LGU's
    overall typical relief-operation scale, distinct from the month-specific
    lag features)."""
    from app.models.barangay import Barangay

    out = {}
    for lgu in lgus:
        barangays = Barangay.query.filter_by(city_municipality=lgu).all()
        population = sum(_to_number(b.population) or 0 for b in barangays)
        risk_vals = [
            _to_number(b.disaster_risk_index) for b in barangays
            if _to_number(b.disaster_risk_index) is not None
        ]
        disaster_risk_index = sum(risk_vals) / len(risk_vals) if risk_vals else None
        monthly_totals = [monthly_table.get((lgu, m), {}).get("total", 0) for m in range(1, 13)]
        out[lgu] = {
            "population": population,
            "disaster_risk_index": disaster_risk_index,
            "historical_allocation": sum(monthly_totals) / 12.0,
        }
    return out


def build_lgu_month_features(lgus=None):
    """The full feature table the model is trained on and later forecasts
    from: one row per (LGU, month 1-12), in FEATURES order, plus the raw
    calibration total for that exact month when one exists (the label).

    lag_1/lag_3/rolling_mean_3 are computed CIRCULARLY over the 12-month
    cycle (December wraps to January) - see the module docstring on why
    this models a representative seasonal cycle rather than a multi-year
    trend.

    Returns {(lgu, month): {"features": [...], "total": int_or_None}}.
    """
    from app.models.office import Office

    if lgus is None:
        lgus = sorted({o.area_covered for o in Office.query.filter_by(office_type="cswdo").all()})

    monthly_table = _load_monthly_lgu_rows()
    scale = _lgu_scale_features(lgus, monthly_table)

    cycles = {
        lgu: [monthly_table.get((lgu, m), {}).get("total", 0) for m in range(1, 13)]
        for lgu in lgus
    }

    result = {}
    for lgu in lgus:
        vals = cycles[lgu]
        for month in range(1, 13):
            idx = month - 1
            entry = monthly_table.get((lgu, month))
            angle = 2 * math.pi * month / 12.0
            feat = {
                "month_sin": math.sin(angle),
                "month_cos": math.cos(angle),
                "lag_1": vals[(idx - 1) % 12],
                "lag_3": vals[(idx - 3) % 12],
                "rolling_mean_3": sum(vals[(idx - k) % 12] for k in (1, 2, 3)) / 3.0,
                "active_disaster_events": len(entry["event_names"]) if entry else 0,
                "population": scale[lgu]["population"],
                "disaster_risk_index": scale[lgu]["disaster_risk_index"],
                "historical_allocation": scale[lgu]["historical_allocation"],
            }
            result[(lgu, month)] = {
                "features": [feat[f] for f in FEATURES],
                "total": entry["total"] if entry else None,
            }
    return result


def _load_training_rows():
    """Labeled examples = one row per (LGU, month) with at least one trusted
    calibration AllocationRecord - see build_lgu_month_features. A month
    with no calibration evidence for an LGU is excluded from training (its
    feature row still exists for forecasting, driven by neighboring months'
    lag/rolling values, but there's no real total to learn from for that
    exact month)."""
    table = build_lgu_month_features()
    X, y = [], []
    for row in table.values():
        if row["total"] is None:
            continue
        X.append(row["features"])
        y.append(row["total"])
    return np.array(X, dtype=float), np.array(y, dtype=float), table


def build_pipeline():
    """Median-impute -> standardize -> Linear Regression.

    The imputer is what lets an incomplete real-world profile still produce
    a forecast; keep_empty_features handles the edge case where a whole
    predictor column is missing from a freshly-loaded dataset."""
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
        ("linreg", LinearRegression()),
    ])


def _safe_mape(y, preds):
    """MAPE over the rows where the actual is non-zero - a zero actual makes
    the percentage undefined, and a relief allocation is never legitimately 0."""
    mask = y != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y[mask] - preds[mask]) / y[mask])) * 100)


def evaluate_loocv(X, y):
    """Leave-one-out CV - each fold refits build_pipeline() from scratch so
    the held-out point never influences its own prediction. Returns pooled
    out-of-fold predictions plus MAE/RMSE/MAPE/R² over that pooled set
    (per-fold R² is undefined with a single test point)."""
    loo = LeaveOneOut()
    preds = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in loo.split(X):
        pipe = build_pipeline()
        pipe.fit(X[train_idx], y[train_idx])
        preds[test_idx] = pipe.predict(X[test_idx])

    # An LGU's monthly demand is never negative - clamp, same as app.ml.predict.
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
            paired_y = y[~np.isnan(col)]
            corr = float(np.corrcoef(present, paired_y)[0, 1])
        else:
            corr = float("nan")
        report["features"][name] = {
            "missing": missing,
            "missing_pct": round(100 * missing / n, 1) if n else 0.0,
            "corr_with_target": round(corr, 3) if corr == corr else None,
        }

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
                            f"{FEATURES[i]} ~ {FEATURES[j]} (r={r:.2f}) - coefficients "
                            f"for these two will be unstable until they carry independent signal"
                        )
    return report


def train_and_persist():
    """Fits the final model on all trusted LGU-month history, records honest
    leave-one-out metrics to ModelMetrics, and saves the fitted pipeline
    (plus the full 12-month-per-LGU feature table, needed to forecast any
    future month) to disk for app.ml.predict to load."""
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    X, y, table = _load_training_rows()
    if len(y) < MIN_TRAINING_SAMPLES:
        raise RuntimeError(
            f"Only {len(y)} labeled LGU-month records found - need at least "
            f"{MIN_TRAINING_SAMPLES} to train a model that isn't pure noise. "
            f"Run scripts/seed_training_data.py and scripts/seed_seasonal_events.py first."
        )

    quality = data_quality_report(X, y)
    metrics = evaluate_loocv(X, y)

    final_pipeline = build_pipeline()
    final_pipeline.fit(X, y)

    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    joblib.dump({
        "pipeline": final_pipeline,
        "features": FEATURES,
        "version": MODEL_VERSION,
        "trained_at": ph_now().isoformat(),
        "training_rows": len(y),
        # Full (lgu, month) -> feature-row table, including months with no
        # calibration total - forecast_lgu/forecast_barangay in
        # app.ml.predict look up any future month here rather than
        # recomputing features (and re-hitting the DB) on every call.
        "lgu_month_table": table,
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
