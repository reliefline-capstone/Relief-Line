"""
Loads the SARIMAX time-series forecaster trained by app.ml.train and projects
monthly food-pack demand for an LGU (forecast_lgu) or, via a top-down split,
for a single barangay (forecast_barangay).

Every forecast month carries two numbers:
  projected_packs - EXPECTED demand (log-normal mean of the forecast)
  p90_packs       - SAFETY-STOCK level: demand stays at or below it 9 months
                    out of 10. Pre-positioning is about not running out, so
                    stock toward P90, not the average.
The horizon has the same pair (horizon_total, horizon_p90). horizon_p90 is
NOT the sum of monthly P90s - storms hit a whole LGU at once, so summing
would overstate it; it is the 90th percentile of the simulated 'total over
these months' (see app.ml.train.SIM_DRAWS).

Barangay split: an LGU forecast is shared out by
    0.6 x (barangay's share of the LGU's recorded history)
  + 0.4 x (households x flood-susceptibility weight)
so a barangay with a track record and/or high flood hazard carries more of
the projected need. Shares sum to 1, so barangay forecasts always add up to
the LGU forecast.

predict_quantity(barangay) is kept as a thin, backward-compatible wrapper -
"this month's" expected demand from forecast_barangay(barangay, 1) - so every
existing call site keeps working. New code wanting a multi-month horizon or
the safety stock should call forecast_barangay/forecast_lgu directly.
"""
import json
from datetime import date

from app.utils.timezone import ph_today

import joblib
import numpy as np

from app.ml.train import (
    ARTIFACT_PATH, MONTH_LABELS, historical_allocation_for,
    historical_allocations_for_many, _to_number,
)
from app.ml import climate_reference as ref

HISTORY_WEIGHT = 0.6
# Relative vulnerability by flood-susceptibility class (1 low .. 4 very high).
VULNERABILITY_WEIGHT = {1: 0.50, 2: 0.85, 3: 1.20, 4: 1.60}

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
        else:
            # An artifact from the old regression model has no time-series
            # forecasts - treat it as "not trained" rather than crash.
            if "forecasts" not in _cached_artifact:
                _cached_artifact = None
    return _cached_artifact


def is_model_available():
    return _load_artifact() is not None


def _start_date(start_month):
    """First day of the first forecast month: the current Philippine month by
    default; a given calendar month (1-12) resolves to its next occurrence
    on/after the current month."""
    today = ph_today()
    if not start_month or start_month == today.month:
        return date(today.year, today.month, 1)
    year = today.year if start_month > today.month else today.year + 1
    return date(year, start_month, 1)


def _add_months(d, n):
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


def forecast_lgu(lgu, months_ahead, start_month=None):
    """Monthly demand projection for `lgu` (a Barangay.city_municipality /
    Office.area_covered value) over the next `months_ahead` months. Returns
    None if no model is trained, the LGU is unknown, or the requested window
    runs past the forecast the artifact carries (retrain to extend it)."""
    artifact = _load_artifact()
    if artifact is None or lgu not in artifact["forecasts"]:
        return None
    table = artifact["forecasts"][lgu]
    keys = artifact["months"]
    start = _start_date(start_month)

    months, positions = [], []
    for i in range(months_ahead):
        d = _add_months(start, i)
        key = d.strftime("%Y-%m")
        row = table.get(key)
        if row is None:
            return None
        positions.append(keys.index(key))
        months.append({
            "month": d.month, "year": d.year,
            "label": MONTH_LABELS[d.month - 1],
            "date": key,
            "projected_packs": max(int(round(row["expected"])), 0),
            "p90_packs": max(int(round(row["p90"])), 0),
            "is_wet_season": d.month in ref.WET_SEASON_MONTHS,
            "is_peak_season": d.month in ref.PEAK_MONTHS,
        })

    total = sum(m["projected_packs"] for m in months)
    paths = artifact["paths"][lgu][positions, :]
    sims = paths.sum(axis=0)
    horizon_p90 = max(int(round(float(np.quantile(sims, 0.9)))), total)

    # Running totals for the "will the stock last?" chart: cumulative expected
    # demand, and the 90th percentile of the cumulative simulated demand at
    # each month (a true percentile of the running total - not a sum of
    # monthly P90s).
    cum_p90 = np.quantile(np.cumsum(paths, axis=0), 0.9, axis=1)
    running = 0
    for m, cp in zip(months, cum_p90):
        running += m["projected_packs"]
        m["cum_expected"] = running
        m["cum_p90"] = max(int(round(float(cp))), running)
    months[-1]["cum_p90"] = horizon_p90
    return {
        "lgu": lgu,
        "months": months,
        "horizon_total": total,
        "horizon_p90": horizon_p90,
        "model_version": artifact.get("version"),
        "data_through": artifact.get("data_through"),
    }


def backtest_series(lgu):
    """Actual vs forecast for the latest backtest year (see
    app.ml.train._latest_fold_series), or None if unavailable."""
    artifact = _load_artifact()
    if artifact is None:
        return None
    return (artifact.get("backtest_series") or {}).get(lgu)


def _barangay_share(barangay):
    """This barangay's share of its LGU's forecast (see module doc)."""
    return _lgu_shares(barangay.city_municipality).get(barangay.barangay_id, 0.0)


def _lgu_shares(lgu):
    """{barangay_id: share} - see share_breakdown for how each is built."""
    return {r["barangay_id"]: r["share"] for r in share_breakdown(lgu)}


def share_breakdown(lgu):
    """Every barangay's share of its LGU's forecast AND the pieces it is
    built from, so the split can be shown and explained on screen:

        share = 0.6 x history_share + 0.4 x vulnerability_share
        history_share       = barangay's packs on record / LGU's packs on record
        vulnerability_share = (households x flood weight) / sum over the LGU

    Cached on flask.g for the length of the current request only, so the map
    endpoint - which forecasts every barangay - computes it once per LGU, and
    it can never go stale across requests. Returns a list of dicts."""
    from flask import g, has_app_context
    from sqlalchemy import bindparam, text
    from app.extensions import db
    from app.models.barangay import Barangay

    cache = None
    if has_app_context():
        cache = g.__dict__.setdefault("_lgu_share_cache", {})
        if lgu in cache:
            return cache[lgu]

    barangays = Barangay.query.filter_by(city_municipality=lgu).all()
    if not barangays:
        return []
    ids = [b.barangay_id for b in barangays]
    hist = {bid: 0.0 for bid in ids}
    history = text(
        "SELECT barangay_id, SUM(food_packs) FROM barangay_monthly_history "
        "WHERE barangay_id IN :ids GROUP BY barangay_id"
    ).bindparams(bindparam("ids", expanding=True))
    for bid, packs in db.session.execute(history, {"ids": ids}).fetchall():
        hist[bid] = float(packs or 0)

    weight = {
        b.barangay_id: VULNERABILITY_WEIGHT.get(int(b.flood_susceptibility or 2), 0.85)
        for b in barangays
    }
    vuln = {b.barangay_id: (_to_number(b.num_households) or 0) * weight[b.barangay_id] for b in barangays}
    h_total, v_total = sum(hist.values()), sum(vuln.values())
    even = 1.0 / len(ids)

    rows = []
    for b in barangays:
        bid = b.barangay_id
        h = hist[bid] / h_total if h_total > 0 else None
        v = vuln[bid] / v_total if v_total > 0 else even
        rows.append({
            "barangay_id": bid,
            "name": b.barangay_name,
            "households": int(_to_number(b.num_households) or 0),
            "flood_susceptibility": int(b.flood_susceptibility or 2),
            "hazard_source": b.hazard_source,
            "flood_weight": weight[bid],
            "history_packs": int(hist[bid]),
            "history_share": h,
            "vulnerability_share": v,
            "share": v if h is None else HISTORY_WEIGHT * h + (1 - HISTORY_WEIGHT) * v,
        })

    if cache is not None:
        cache[lgu] = rows
    return rows


def forecast_barangay(barangay, months_ahead, start_month=None):
    """Per-barangay breakdown of forecast_lgu (top-down split - see module
    doc). Returns None if no model has been trained yet."""
    lgu_forecast = forecast_lgu(barangay.city_municipality, months_ahead, start_month)
    if lgu_forecast is None:
        return None
    share = _barangay_share(barangay)
    months = [
        {**m,
         "projected_packs": max(int(round(m["projected_packs"] * share)), 0),
         "p90_packs": max(int(round(m["p90_packs"] * share)), 0)}
        for m in lgu_forecast["months"]
    ]
    return {
        "barangay_id": barangay.barangay_id,
        "lgu": barangay.city_municipality,
        "months": months,
        "horizon_total": sum(m["projected_packs"] for m in months),
        "horizon_p90": max(int(round(lgu_forecast["horizon_p90"] * share)),
                           sum(m["projected_packs"] for m in months)),
        "model_version": lgu_forecast["model_version"],
        "data_through": lgu_forecast["data_through"],
        "share": round(share, 4),
    }


def predict_quantity(barangay):
    """Backward-compatible single-number estimate for one barangay - this
    month's EXPECTED demand, or None if no model has been trained yet."""
    result = forecast_barangay(barangay, months_ahead=1)
    if result is None or not result["months"]:
        return None
    return result["months"][0]["projected_packs"]


def predict_safety_stock(barangay):
    """This month's P90 safety-stock level for one barangay (None if no
    model). Stock toward this, not the expected value, when pre-positioning."""
    result = forecast_barangay(barangay, months_ahead=1)
    if result is None or not result["months"]:
        return None
    return result["months"][0]["p90_packs"]


def log_prediction_once_per_day(barangay, predicted_quantity):
    """Writes a real PredictionLog row (input snapshot + output), deduped per
    barangay per day so repeated page loads don't spam the table with
    identical rows. The snapshot records what actually drove the number: the
    LGU forecast (expected / P90 for the month), this barangay's share of
    it, and how fresh the training data was."""
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

    lgu_month = forecast_lgu(barangay.city_municipality, 1)
    row = lgu_month["months"][0] if lgu_month else None
    snapshot = {
        "lgu": barangay.city_municipality,
        "month": _start_date(None).strftime("%Y-%m"),
        "lgu_expected": row["projected_packs"] if row else None,
        "lgu_p90": row["p90_packs"] if row else None,
        "barangay_share": round(_barangay_share(barangay), 4),
        "data_through": artifact.get("data_through"),
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
