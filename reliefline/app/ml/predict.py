"""
Loads the LGU-level time-forecasting model trained by app.ml.train and
projects food-pack demand over future calendar months for a given LGU
(forecast_lgu) or, via a top-down proportional split, a given barangay
(forecast_barangay) - see app.ml.train's module docstring for why the model
forecasts at LGU level rather than per barangay.

predict_quantity(barangay) is kept as a thin, backward-compatible wrapper -
"this month's" slice of forecast_barangay(barangay, months_ahead=1) - so
every existing call site (Predictive Analytics ranking, Relief Request
review, proactive/direct allocation) that just needs one current number
keeps working unchanged. New code that wants a multi-month horizon should
call forecast_barangay/forecast_lgu directly.
"""
import json

from app.utils.timezone import ph_today

import joblib

from app.ml.train import (
    ARTIFACT_PATH, FEATURES, MONTH_LABELS, historical_allocation_for,
    historical_allocations_for_many, _to_number,
)

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


def forecast_lgu(lgu, months_ahead, start_month=None):
    """Projects total food-pack demand for `lgu` (a Barangay.city_municipality
    / Office.area_covered value, e.g. "Urdaneta City") over the next
    `months_ahead` calendar months. Returns None if no model has been
    trained yet (see scripts/train_model.py).

    start_month (1-12) defaults to the current real month. Walks the
    fitted "representative annual cycle" forward, wrapping December back to
    January - each month's projection comes straight from the trained
    pipeline applied to that (lgu, month)'s stored feature row (see
    app.ml.train.build_lgu_month_features), not a recursive multi-step
    simulation, since the model already represents one typical year rather
    than tracking year-over-year drift (see app.ml.train's module docstring).
    """
    artifact = _load_artifact()
    if artifact is None:
        return None
    table = artifact.get("lgu_month_table", {})
    pipeline = artifact["pipeline"]
    start_month = start_month or ph_today().month

    months = []
    total = 0
    for i in range(months_ahead):
        m = ((start_month - 1 + i) % 12) + 1
        row = table.get((lgu, m))
        projected = 0
        if row is not None:
            raw = pipeline.predict([row["features"]])[0]
            projected = max(int(round(raw)), 0)
        months.append({"month": m, "label": MONTH_LABELS[m - 1], "projected_packs": projected})
        total += projected

    return {
        "lgu": lgu,
        "months": months,
        "horizon_total": total,
        "model_version": artifact.get("version"),
    }


def _barangay_share(barangay):
    """This barangay's proportional share of its LGU's forecast. A barangay
    with a real historical_allocation on record is weighted by that figure;
    one with none yet falls back to a population-scaled weight, using the
    packs-per-population ratio observed among barangays in the same LGU that
    do have history (0.05 - a rough mid-range estimate from the synthetic
    generative model - only when literally no barangay in the LGU has any
    history at all to derive a real ratio from)."""
    return _lgu_shares(barangay.city_municipality).get(barangay.barangay_id, 0.0)


def _lgu_shares(lgu):
    """Every barangay's share of its LGU's forecast, for the whole LGU at
    once (2 queries total). Cached on flask.g for the length of the current
    request only, so the map endpoint - which forecasts every barangay,
    each of which needs the same LGU-wide split - computes it once per LGU
    instead of once per barangay, and it can never go stale across requests
    (allocations approved a moment ago are always reflected on the next
    load). Outside a request it just computes fresh each time."""
    from flask import g, has_app_context
    from app.models.barangay import Barangay

    cache = None
    if has_app_context():
        cache = g.__dict__.setdefault("_lgu_share_cache", {})
        if lgu in cache:
            return cache[lgu]

    lgu_barangays = Barangay.query.filter_by(city_municipality=lgu).all()
    hist = historical_allocations_for_many([b.barangay_id for b in lgu_barangays])
    pops = {b.barangay_id: (_to_number(b.population) or 0) for b in lgu_barangays}

    known = [(hist[bid], pops[bid]) for bid in hist if hist[bid] > 0 and pops[bid] > 0]
    avg_ratio = (sum(h for h, _p in known) / sum(p for _h, p in known)) if known else 0.05

    weights = {bid: (hist[bid] if hist[bid] > 0 else pops[bid] * avg_ratio) for bid in hist}
    total = sum(weights.values())
    if total <= 0:
        even = 1.0 / len(lgu_barangays) if lgu_barangays else 0.0
        shares = {bid: even for bid in hist}
    else:
        shares = {bid: weights[bid] / total for bid in hist}

    if cache is not None:
        cache[lgu] = shares
    return shares


def forecast_barangay(barangay, months_ahead, start_month=None):
    """Per-barangay breakdown of forecast_lgu - a top-down proportional
    split (see _barangay_share), since the model itself forecasts at LGU
    level. Returns None if no model has been trained yet."""
    lgu_forecast = forecast_lgu(barangay.city_municipality, months_ahead, start_month)
    if lgu_forecast is None:
        return None
    share = _barangay_share(barangay)
    months = [
        {**m, "projected_packs": max(int(round(m["projected_packs"] * share)), 0)}
        for m in lgu_forecast["months"]
    ]
    return {
        "barangay_id": barangay.barangay_id,
        "lgu": barangay.city_municipality,
        "months": months,
        "horizon_total": sum(m["projected_packs"] for m in months),
        "model_version": lgu_forecast["model_version"],
        "share": round(share, 4),
    }


def predict_quantity(barangay):
    """Backward-compatible single-number estimate for one barangay - this
    month's projected demand, or None if no model has been trained yet.
    Every pre-existing call site (Predictive Analytics, Relief Request
    review, proactive/direct allocation) uses this; a new caller wanting a
    multi-month horizon should call forecast_barangay directly instead."""
    result = forecast_barangay(barangay, months_ahead=1)
    if result is None or not result["months"]:
        return None
    return result["months"][0]["projected_packs"]


def log_prediction_once_per_day(barangay, predicted_quantity):
    """Writes a real PredictionLog row (input snapshot + output), deduped per
    barangay per day so repeated page loads don't spam the table with
    identical rows. The snapshot now reflects the LGU-month features that
    actually drove the forecast, plus this barangay's proportional share of
    its LGU's total - the model's real inputs, not per-barangay attributes
    it no longer reads directly (see app.ml.train)."""
    from app.extensions import db
    from app.models.prediction import PredictionLog

    artifact = _load_artifact()
    if artifact is None:
        return None

    existing = PredictionLog.query.filter(
        PredictionLog.barangay_id == barangay.barangay_id,
        PredictionLog.model_version == artifact["version"],
        db.func.date(PredictionLog.predicted_at) == ph_today(),
    ).first()
    if existing:
        return existing

    month = ph_today().month
    table = artifact.get("lgu_month_table", {})
    row = table.get((barangay.city_municipality, month))
    snapshot = {
        "lgu": barangay.city_municipality,
        "month": month,
        "lgu_features": dict(zip(FEATURES, row["features"])) if row else None,
        "barangay_share": round(_barangay_share(barangay), 4),
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
