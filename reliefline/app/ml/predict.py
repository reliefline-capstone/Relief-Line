"""
Loads the two-stage forecaster trained by app.ml.train and projects food-pack
demand for an LGU (forecast_lgu) or, via a barangay-share split, for a single
barangay (forecast_barangay).

Every forecast month carries two numbers:
  projected_packs - EXPECTED demand (Stage 2's severity.expected scenario)
  p90_packs       - SAFETY-STOCK level (Stage 2's severity.high / 90th
                     percentile scenario). Pre-positioning is about not
                     running out, so stock toward P90, not the average.
The horizon has the same pair (horizon_total, horizon_p90).

Formula (see app.ml.train module doc for the full rationale):
  stock = expected_typhoons(horizon) x P(relief) x total_packs(scenario)
          x barangay_share x (1 + buffer)

expected_typhoons(horizon) is CLIMATOLOGICAL (Stage 2's per-calendar-month
typhoon rate, summed over the horizon's months - see _forecast_window) and
anchored to the real current date: a horizon run in December over Jan-Mar can
climatologically total ~0 expected typhoons (no historical Dec-May storms),
which is correct behavior, not a bug - see app.ml.train.climatology_by_month.

Barangay split: forecast_lgu's total is shared out by Stage 1's share -
the regression share (clip(slope x total_families + intercept, 0)) blended
with the barangay's own relief history, with a per-family floor so no
barangay is left near zero - see app.ml.train.predict_shares.
Shares always sum to 1, so barangay forecasts always add up to the LGU
forecast.

predict_quantity(barangay) is kept as a thin, backward-compatible wrapper -
"this month's" expected demand from forecast_barangay(barangay, 1) - so every
existing call site keeps working. New code wanting a multi-month horizon or
the safety stock should call forecast_barangay/forecast_lgu directly.
"""
import json
from datetime import date

from app.utils.timezone import ph_today

import joblib

from app.ml.train import (
    ARTIFACT_PATH, MONTH_LABELS, historical_allocation_for,
    historical_allocations_for_many, _to_number, predict_shares,
)
from app.ml import climate_reference as ref

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
            # An artifact from an older model version has no "lgu"/"climatology"
            # keys - treat it as "not trained" rather than crash.
            if "lgu" not in _cached_artifact or "climatology" not in _cached_artifact:
                _cached_artifact = None
    return _cached_artifact


def is_model_available():
    return _load_artifact() is not None


def _add_months(d, n):
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


def _forecast_window(months_ahead, start_month=None, include_current=False):
    """The ordered list of calendar months this forecast covers, as date
    objects (first of month). THIS is the single place "how does a horizon
    anchor to today" lives - confirmed: start from the NEXT FULL calendar
    month (no prorating the remainder of the current month - stock lead time
    makes a partial current month not actionable). A specific `start_month`
    (1-12) resolves to its next occurrence on/after next month.

    `include_current` anchors at the current calendar month instead - used only
    to DRAW the current month on the Projected Demand chart; the stock-planning
    totals keep the next-full-month anchor above."""
    today = ph_today()
    base = _add_months(date(today.year, today.month, 1), 0 if include_current else 1)
    if start_month and start_month != base.month:
        year = base.year if start_month > base.month else base.year + 1
        base = date(year, start_month, 1)
    return [_add_months(base, i) for i in range(months_ahead)]


def forecast_lgu(lgu, months_ahead, start_month=None, include_current=False):
    """Food-pack demand projection for `lgu` (a Barangay.city_municipality /
    Office.area_covered value) over the next `months_ahead` months, starting
    from the next full calendar month. Returns None if no model is trained or
    the LGU has no fitted share model."""
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
    lgu_expected_total = expected_typhoons * L["p_relief"] * L["severity"]["expected"] * (1 + buffer)
    lgu_p90_total = expected_typhoons * L["p_relief"] * L["severity"]["high"] * (1 + buffer)

    months = []
    running_e = running_p = 0
    for d, rate in zip(window, monthly_rate):
        # No signal exists within the horizon beyond the climatological rate
        # itself, so each month's share of the horizon total is its own
        # share of the horizon's summed rate (0 for every month if the whole
        # horizon has 0 expected typhoons - climatologically correct, see
        # module doc).
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
    horizon_p90 = max(int(round(lgu_p90_total)), total)
    if months:
        months[-1]["cum_p90"] = horizon_p90
    # Reported separately so the buffer stays a visible policy choice and
    # never silently absorbs a change in the percentile itself.
    p90_before_buffer = int(round(lgu_p90_total / (1 + buffer)))
    largest_event = int(round(L["severity"].get("max") or 0))
    per_event_p90 = int(round(L["severity"]["high"]))
    return {
        "lgu": lgu, "months": months,
        "horizon_total": total, "horizon_p90": horizon_p90,
        "p90_before_buffer": p90_before_buffer,
        "buffer": buffer, "buffer_packs": horizon_p90 - p90_before_buffer,
        "expected_typhoons": expected_typhoons,
        "expected_relief_events": expected_typhoons * L["p_relief"],
        "per_event_p90": per_event_p90,
        # Known limits (2026-10-03). The horizon P90 is expected storms x
        # P(relief) x the per-EVENT P90, not the P90 of a multi-storm total,
        # so it scales one bad storm down by the expected number of relief
        # events. When that's under 1, the stockpile is smaller than a single
        # 90th-percentile relief operation - not a safety stock. Keyed to
        # the window's expected relief events, not its length: from a
        # November start the 3- and 6-month windows hold the same ~1 typhoon
        # (Dec-May has almost none), so a month count can't tell them apart.
        "short_horizon": p90_before_buffer < per_event_p90,
        "largest_event": largest_event,
        # Compared WITHOUT the buffer: whether the 15% buffer should count
        # as coverage is a policy decision, so it's reported, not assumed.
        "below_largest_event": largest_event > p90_before_buffer,
        "largest_covered_only_by_buffer": p90_before_buffer < largest_event <= horizon_p90,
        "model_version": artifact.get("version"), "data_through": artifact.get("data_through"),
    }


def loto_cv_summary():
    """Per-LGU leave-one-typhoon-out validation: the share model's own MAE
    against the equal-split and average-share baselines (see
    app.ml.train.leave_one_typhoon_out_cv), sorted by LGU name. ModelMetrics.mae
    only stores the single worst-LGU value (one row, one column can't hold
    three); this is the full per-LGU picture for the dashboard. [] if no
    model is trained or no LGU had enough events to validate."""
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
            # Size-weighted scores (v9.1+); None on an older artifact.
            "mae_model_weighted": cv.get("mae_model_weighted"),
            "mae_equal_split_weighted": cv.get("mae_equal_split_weighted"),
            "mae_avg_share_weighted": cv.get("mae_avg_share_weighted"),
            # Pooled-history baseline + k-of-n + bootstrap CI (v9.2+).
            "mae_pooled_history_weighted": cv.get("mae_pooled_history_weighted"),
            "beats_pooled_k": cv.get("beats_pooled_k"),
            "beats_pooled_n": cv.get("beats_pooled_n"),
            "diff_vs_pooled_weighted_ci": cv.get("diff_vs_pooled_weighted_ci"),
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


def loto_packs_cv_summary():
    """Per-LGU leave-one-typhoon-out validation of the full pipeline's
    pack-count predictions (see app.ml.train.leave_one_typhoon_out_packs_cv) -
    MAE/RMSE in packs. [] if no model is trained or no LGU had enough events."""
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
            "n": cv["n"],
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


def p90_coverage_summary():
    """Per-LGU leave-one-typhoon-out check of the P90 promise itself: how
    often did the real outcome actually stay at/below the recommended P90
    stockpile (see app.ml.train.leave_one_typhoon_out_p90_coverage)? Target
    ~90%. [] if no model is trained or no LGU had enough events."""
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
        })
    rows.sort(key=lambda r: r["lgu"])
    return rows


def backtest_series(lgu):
    """Actual vs. leave-one-typhoon-out prediction for every real relief
    event this LGU has on record (see app.ml.train._backtest_points) - the
    event-based analogue of the old rolling-origin monthly backtest. None if
    unavailable."""
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
    """Every barangay's share of its LGU's forecast, from Stage 1
    (app.ml.train.predict_shares): the regression share
    clip(slope x total_families + intercept, 0), blended with the barangay's
    pooled relief history by the LGU's tuned alpha, then floored so no
    barangay gets less than SHARE_FLOOR x its per-family share - shares
    always sum to 1 across the LGU.
    `total_families` is each barangay's most recent known family-count
    snapshot from a real relief record, falling back to its current
    num_households if it has never appeared in one.

    Cached on flask.g for the length of the current request only, so the map
    endpoint - which forecasts every barangay - computes it once per LGU, and
    it can never go stale across requests. Returns a list of dicts."""
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

    # v9.2+: regression blended with each barangay's pooled relief history,
    # then the per-family floor (app.ml.train.predict_shares). An older
    # artifact has no history/alpha/floor -> plain regression split.
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
            "flood_susceptibility": None,   # vulnerability blending dropped, see share_breakdown doc
            "hazard_source": None,
            "flood_weight": None,
            "history_packs": 0,
            # Share of the LGU's past relief this barangay received (None if
            # it has never appeared in a relief record).
            "history_share": history.get(bid),
            "vulnerability_share": None,
            # True when the floor lifted this barangay to its minimum.
            "floor_applied": floor > 0 and family_share > 0 and share <= floor * family_share + 1e-9,
            "share": share,
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
