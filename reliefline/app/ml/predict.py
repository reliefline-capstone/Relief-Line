# Uses the trained model to forecast food pack needs per municipality and barangay.

import json
from datetime import date

from app.utils.timezone import ph_today

import joblib

from app.ml.train import (
    ARTIFACT_PATH, MONTH_LABELS, historical_allocation_for,
    _to_number, predict_shares,
)
from app.ml import climate_reference as ref

_cached_artifact = None
_load_attempted = False


# Loads the trained forecast model file (app/ml/artifacts/food_pack_demand.joblib).
# It is loaded only once and then reused, so pages stay fast.
def _load_artifact():
    global _cached_artifact, _load_attempted
    if not _load_attempted:
        _load_attempted = True
        try:
            _cached_artifact = joblib.load(ARTIFACT_PATH)
        except FileNotFoundError:
            _cached_artifact = None
        else:
            if "lgu" not in _cached_artifact or "climatology" not in _cached_artifact:
                _cached_artifact = None
    return _cached_artifact


# True if a trained forecast model file is available.
def is_model_available():
    return _load_artifact() is not None


# Moves a date forward by a number of months (e.g. October + 3 = January).
def _add_months(d, n):
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


# Lists the months to forecast, e.g. the next 12 months starting next month
# (or starting from a chosen month).
def _forecast_window(months_ahead, start_month=None, include_current=False):
    today = ph_today()
    base = _add_months(date(today.year, today.month, 1), 0 if include_current else 1)
    if start_month and start_month != base.month:
        year = base.year if start_month > base.month else base.year + 1
        base = date(year, start_month, 1)
    return [_add_months(base, i) for i in range(months_ahead)]


# Forecasts how many food packs a municipality will need, month by month.
# Gives the expected need, and the recommended stockpile (high/P90 estimate plus the 15% safety buffer).
def forecast_lgu(lgu, months_ahead, start_month=None, include_current=False):
    artifact = _load_artifact()
    if artifact is None or lgu not in artifact["lgu"]:
        return None
    L = artifact["lgu"][lgu]
    climatology = artifact["climatology"]
    buffer = artifact["buffer"]
    window = _forecast_window(months_ahead, start_month, include_current)
    today = ph_today()

    monthly_rate = [climatology.get(d.month, 0.0) for d in window]
    expected_typhoons = sum(monthly_rate)
    relief_events = expected_typhoons * L["p_relief"]
    # Expected need = how many relief operations to expect x packs a typical typhoon needs.
    lgu_expected_total = relief_events * L["severity"]["expected"]
    lgu_p90_raw = relief_events * L["severity"]["high"]
    # Recommended stockpile = high (P90) need plus the 15% safety buffer.
    lgu_p90_total = lgu_p90_raw * (1 + buffer)

    months = []
    running_e = running_p = 0
    for d, rate in zip(window, monthly_rate):
        frac = (rate / expected_typhoons) if expected_typhoons > 0 else 0.0
        proj = max(int(round(lgu_expected_total * frac)), 0)
        p90 = max(int(round(lgu_p90_total * frac)), proj)
        running_e += proj
        running_p = max(running_p + p90, running_e)
        months.append({
            "month": d.month, "year": d.year, "label": MONTH_LABELS[d.month - 1],
            "date": d.strftime("%Y-%m"),
            "is_current": (d.year, d.month) == (today.year, today.month),
            "projected_packs": proj, "p90_packs": p90,
            "is_wet_season": d.month in ref.WET_SEASON_MONTHS,
            "is_peak_season": d.month in ref.PEAK_MONTHS,
            "cum_expected": running_e, "cum_p90": running_p,
        })

    total = sum(m["projected_packs"] for m in months)
    p90_before_buffer = int(round(lgu_p90_raw))
    horizon_p90 = max(int(round(lgu_p90_total)), total)
    if months:
        months[-1]["cum_p90"] = horizon_p90
    largest_event = int(round(L["severity"].get("max") or 0))
    per_event_p90 = int(round(L["severity"]["high"]))
    yearly = L.get("yearly_totals") or {}
    largest_year = max(yearly, key=yearly.get) if yearly else None
    largest_year_total = int(round(yearly[largest_year])) if largest_year is not None else None
    return {
        "lgu": lgu, "months": months,
        "horizon_total": total, "horizon_p90": horizon_p90,
        "p90_before_buffer": p90_before_buffer,
        "buffer": buffer, "buffer_packs": horizon_p90 - p90_before_buffer,
        "expected_typhoons": expected_typhoons,
        "expected_relief_events": relief_events,
        "per_event_p90": per_event_p90,
        "short_horizon": p90_before_buffer < per_event_p90,
        "largest_event": largest_event,
        "below_largest_event": largest_event > p90_before_buffer,
        "largest_covered_only_by_buffer": p90_before_buffer < largest_event <= horizon_p90,
        "largest_year": largest_year, "largest_year_total": largest_year_total,
        "below_largest_year": (largest_year_total or 0) > p90_before_buffer,
        "model_version": artifact.get("version"), "data_through": artifact.get("data_through"),
    }


# Accuracy results of the 'how packs are split among barangays' part of the model,
# shown in the Model Accuracy panel (compared with simple guessing methods).
def loto_cv_summary():
    artifact = _load_artifact()
    if artifact is None:
        return []
    rows = []
    for lgu, cv in (artifact.get("loto_cv") or {}).items():
        if not cv:
            continue
        rows.append({
            "lgu": lgu,
            "mae_model": cv["mae_model"],
            "mae_equal_split": cv["mae_equal_split"],
            "mae_avg_share": cv["mae_avg_share"],
            "n_folds": cv["n_folds"],
            "beats_equal_split": cv["mae_model"] <= cv["mae_equal_split"],
            "beats_avg_share": cv["mae_model"] <= cv["mae_avg_share"],
            "mae_model_weighted": cv.get("mae_model_weighted"),
            "mae_equal_split_weighted": cv.get("mae_equal_split_weighted"),
            "mae_avg_share_weighted": cv.get("mae_avg_share_weighted"),
            "mae_pooled_history_weighted": cv.get("mae_pooled_history_weighted"),
            "beats_pooled_k": cv.get("beats_pooled_k"),
            "beats_pooled_n": cv.get("beats_pooled_n"),
            "diff_vs_pooled_weighted_ci": cv.get("diff_vs_pooled_weighted_ci"),
            "skill_vs_pooled": cv.get("skill_vs_pooled"),
            "skill_vs_pooled_ci": cv.get("skill_vs_pooled_ci"),
            "spearman_model": cv.get("spearman_model"),
            "spearman_pooled": cv.get("spearman_pooled"),
            "top_k_model": cv.get("top_k_model"),
            "top_k_pooled": cv.get("top_k_pooled"),
            "top_k": cv.get("top_k"),
            "rank_n_storms": cv.get("rank_n_storms"),
            "floor": cv.get("floor"),
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


# Accuracy results of the food pack forecast, measured in packs,
# shown in the Model Accuracy panel.
def loto_packs_cv_summary():
    artifact = _load_artifact()
    if artifact is None:
        return []
    rows = []
    for lgu, cv in (artifact.get("loto_packs_cv") or {}).items():
        if not cv:
            continue
        rows.append({
            "lgu": lgu,
            "mae_packs": cv["mae_packs"],
            "rmse_packs": cv["rmse_packs"],
            "wape": cv.get("wape"),
            "n": cv["n"],
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


# How often the recommended stockpile would have been enough in past typhoons (target: about 90%).
# Shown in the Model Accuracy panel.
def p90_coverage_summary():
    artifact = _load_artifact()
    if artifact is None:
        return []
    rows = []
    for lgu, cv in (artifact.get("loto_p90") or {}).items():
        if not cv:
            continue
        rows.append({
            "lgu": lgu,
            "lgu_coverage": cv["lgu_coverage"],
            "barangay_coverage": cv["barangay_coverage"],
            "lgu_n": cv["lgu_n"],
            "barangay_n": cv["barangay_n"],
            "barangay_coverage_nonzero": cv.get("barangay_coverage_nonzero"),
            "barangay_nonzero_n": cv.get("barangay_nonzero_n"),
            "lgu_hits": cv.get("lgu_hits"),
            "barangay_nonzero_hits": cv.get("barangay_nonzero_hits"),
            "pinball_lgu": cv.get("pinball_lgu"),
            "pinball_barangay_nonzero": cv.get("pinball_barangay_nonzero"),
            "shortfall_lgu": cv.get("shortfall_lgu"),
            "shortfall_barangay_nonzero": cv.get("shortfall_barangay_nonzero"),
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


# Past typhoons: actual packs given vs what the model would have predicted.
# Used for the 'actual vs predicted' chart.
def backtest_series(lgu):
    artifact = _load_artifact()
    if artifact is None:
        return None
    return (artifact.get("backtest_series") or {}).get(lgu)


# This barangay's share (percentage) of its municipality's food pack need.
def _barangay_share(barangay):
    return _lgu_shares(barangay.city_municipality).get(barangay.barangay_id, 0.0)


# Each barangay's share of its municipality's food pack need.
def _lgu_shares(lgu):
    return {r["barangay_id"]: r["share"] for r in share_breakdown(lgu)}


# Splits a municipality's food pack need across its barangays,
# based on each barangay's number of families and how much relief it got in past typhoons.
def share_breakdown(lgu):
    from flask import g, has_app_context
    from app.models.barangay import Barangay

    cache = None
    if has_app_context():
        cache = g.__dict__.setdefault("_lgu_share_cache", {})
        if lgu in cache:
            return cache[lgu]

    artifact = _load_artifact()
    barangays = Barangay.query.filter_by(city_municipality=lgu).all()
    if not barangays or artifact is None or lgu not in artifact["lgu"]:
        return []

    L = artifact["lgu"][lgu]
    model = L["share_model"]
    known = L["barangays"]
    total_families = {}
    for b in barangays:
        snap = known.get(b.barangay_id, {}).get("latest_total_families")
        total_families[b.barangay_id] = snap if snap is not None else (_to_number(b.num_households) or 0)

    history = L.get("history_share") or {}
    alpha = L.get("alpha", 0.0)
    floor = L.get("share_floor", 0.0)
    shares = predict_shares(model, total_families, history, alpha, floor)
    family_total = sum(total_families.values())

    rows = []
    for b in barangays:
        bid = b.barangay_id
        family_share = total_families[bid] / family_total if family_total else 0.0
        share = shares.get(bid, 0.0)
        rows.append({
            "barangay_id": bid,
            "name": b.barangay_name,
            "households": int(_to_number(b.num_households) or 0),
            "total_families_used": int(total_families[bid]),
            "flood_susceptibility": None,
            "hazard_source": None,
            "flood_weight": None,
            "history_packs": 0,
            "history_share": history.get(bid),
            "vulnerability_share": None,
            "floor_applied": floor > 0 and family_share > 0 and share <= floor * family_share + 1e-9,
            "share": share,
        })

    if cache is not None:
        cache[lgu] = rows
    return rows


# Forecasts food packs for one barangay:
# its share of the municipality's forecast, month by month.
def forecast_barangay(barangay, months_ahead, start_month=None):
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


# Next month's expected food packs for one barangay.
def predict_quantity(barangay):
    result = forecast_barangay(barangay, months_ahead=1)
    if result is None or not result["months"]:
        return None
    return result["months"][0]["projected_packs"]


# Saves a barangay's forecast to the database for record keeping,
# at most once a day so page reloads don't create duplicates.
def log_prediction_once_per_day(barangay, predicted_quantity):
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
        "month": _forecast_window(1)[0].strftime("%Y-%m"),
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
