"""
Trains the food-pack TWO-STAGE forecaster: per LGU (Urdaneta City, Santa
Barbara, Calasiao), Stage 1 is a linear regression predicting each
barangay's SHARE of its LGU's relief for a typhoon, and Stage 2 is computed
statistics (not ML) giving how often typhoons happen and how big they are.
Together they answer "how many food packs should this barangay hold in
stock for the next N months?" for PSWDO/CSWDO.

--------------------------------------------------------------------------
Why this replaced the SARIMAX time-series model (v8.0)
--------------------------------------------------------------------------
v8.0 trained on barangay_monthly_history, which was ~97% FABRICATED data
(data_source='synthetic') padding out a monthly series long enough for a
SARIMAX fit. The team paused model work suspecting that fabricated history
was inflated, and gathered real per-typhoon relief records for all three
target LGUs instead (see scripts/real_*.py, scripts/load_relief_events.py -
49 real relief events, 1300+ barangay-level rows, 2021-2026). Real data is
event-based and irregular (one row per typhoon, not one per month), which a
monthly ARIMA-family model can't consume without re-inventing the padding
problem it was already suspect for. Two-stage sidesteps this entirely:

  Stage 1 (share, ML): what fraction of a typhoon's relief does barangay B
  get? This is a STABLE, learnable quantity - it tracks population/exposure,
  not any single storm's severity - and it never needs to know a future
  typhoon's magnitude, so there's no leakage risk forecasting it months
  ahead. Fit by pooling every (relief_event, barangay) row across an LGU's
  whole real history: share = food_packs_given / that event's LGU total,
  regressed on total_families_snapshot (the ONLY predictor - a barangay's
  own affected_families/food_packs_given for a FUTURE typhoon obviously
  can't be a predictor of themselves, and adding total_individuals_snapshot
  alongside total_families_snapshot was tested informally and added nothing,
  since the two are collinear).

  Stage 2 (severity/frequency, computed): how bad is a typical typhoon for
  this LGU, and how often does one hit? Both come straight from real
  records/the verified calendar, not a fitted model - with 8-27 events per
  LGU there isn't enough data to fit a distribution shape, so empirical
  percentiles (25th/mean/90th of real per-typhoon LGU totals) and a simple
  frequency count are the honest choice. Crucially, frequency is CLIMATOLOGICAL
  (how many typhoons has this calendar month historically had, from
  typhoon_calendar - a fact independent of any future storm's existence) so a
  forecast for "next 3 months" run in December can climatologically show ~0
  expected typhoons (Dec-May has none in the record) without needing to
  predict an unknowable future event - see app.ml.predict._forecast_window.

  P(relief) - the chance a typhoon on the calendar actually triggered a
  relief operation for THIS LGU - is deliberately computed from real
  relief-record coverage (p_relief below), NOT from typhoon_calendar's own
  pangasinan_impact_confirmed column: that column is only research-search
  confidence (did a news article name Pangasinan), and real records already
  contradict it for many "not confirmed" storms (Kiko, Jolina, Fabian,
  Karding... all have real Calasiao/Urdaneta relief despite being marked
  "not confirmed in sources reviewed" - a desk search missing a source is not
  the same as relief not happening).

Formula (see app.ml.predict.forecast_lgu for the actual implementation):
  stock(barangay, horizon, scenario) =
      expected_typhoons(horizon) x P(relief) x total_packs(scenario)
      x share(barangay) x (1 + BUFFER)

Validation: leave-one-typhoon-out cross-validation (leave_one_typhoon_out_cv)
against two baselines - equal 1/N split and each barangay's average
historical share - refit on every OTHER event, scored on the held-out one.
An informal check on a 14-typhoon Calasiao subset found LinReg MAE 0.0096 vs
avg-share 0.0100 vs equal-split 0.0191: a real but modest edge over
avg-share, kept because it also gives a sane number to a barangay with
little/no history (avg-share can't).
--------------------------------------------------------------------------
"""
import os
import statistics
from datetime import date

from app.utils.timezone import ph_now, ph_today

import numpy as np
import joblib

MODEL_VERSION = "v9.0-two-stage-lgu"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")

# Safety margin added on top of the formula's raw output, applied uniformly
# to both the expected and P90 totals.
BUFFER = 0.15

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
    realized per-event allocations (records collapsed to one summed figure
    per event first - see _median_event_allocation - so a barangay with
    several installments for one typhoon is counted once per event, not once
    per row). Shown on the admin barangay views and stored on new allocations
    for audit.

    Only 'approved'/'released' records count. Returns 0 for a barangay with
    no realized allocation on record ("no prior allocation" is real
    information, not a missing value). before_date excludes records on/after
    that date so a row can never "see" its own label as its own history.
    """
    from app.models.allocation import AllocationRecord

    q = AllocationRecord.query.filter(
        AllocationRecord.barangay_id == barangay_id,
        AllocationRecord.status.in_(("approved", "released")),
    )
    if before_date is not None:
        q = q.filter(AllocationRecord.allocation_date < before_date)
    return _median_event_allocation(q.all())


def _median_event_allocation(records):
    """The per-barangay figure historical_allocation_for describes, from
    that barangay's already-loaded qualifying records.

    Multiple AllocationRecord rows can share one event_id - checked against
    the real data before changing this (2026-09-28): they're genuinely
    separate allocation batches spread over days/weeks with varying
    quantities (e.g. barangay 43/event 1: 45 packs on 2026-08-28, another 120
    on 2026-09-14), not same-day duplicates or corrections of one another, so
    they're SUMMED per event. (Previously took the max of the group, which
    silently dropped every installment but the largest one.)"""
    if not records:
        return 0

    per_event = {}
    for rec in records:
        key = rec.event_id if rec.event_id is not None else ("solo", rec.allocation_id)
        per_event[key] = per_event.get(key, 0) + _realized_quantity(rec)

    return float(statistics.median(per_event.values()))


def historical_allocations_for_many(barangay_ids, before_date=None):
    """historical_allocation_for for a whole set of barangays in ONE query
    (same filter, same per-event collapsing, same result per id)."""
    from app.models.allocation import AllocationRecord

    ids = list(barangay_ids)
    by_barangay = {bid: [] for bid in ids}
    if not ids:
        return {}
    q = AllocationRecord.query.filter(
        AllocationRecord.barangay_id.in_(ids),
        AllocationRecord.status.in_(("approved", "released")),
    )
    if before_date is not None:
        q = q.filter(AllocationRecord.allocation_date < before_date)
    for rec in q.all():
        by_barangay[rec.barangay_id].append(rec)
    return {bid: _median_event_allocation(recs) for bid, recs in by_barangay.items()}


# ---------------------------------------------------------------------------
# Real relief data (Stage 1 + Stage 2 input)
# ---------------------------------------------------------------------------

def load_relief_data():
    """{lgu: {relief_event_id: {report_date, typhoon_keys, records:[
        {barangay_id, affected_families, affected_individuals,
         food_packs_given, total_families_snapshot, total_individuals_snapshot}
    ]}}} from relief_events / relief_event_typhoons / barangay_relief_records
    (see scripts/apply_relief_schema.py, scripts/load_relief_events.py)."""
    from sqlalchemy import text
    from app.extensions import db

    events = db.session.execute(text(
        "SELECT relief_event_id, city_municipality, report_date FROM relief_events")).fetchall()
    typhoons = db.session.execute(text(
        "SELECT relief_event_id, typhoon_key FROM relief_event_typhoons")).fetchall()
    keys_by_event = {}
    for eid, key in typhoons:
        keys_by_event.setdefault(eid, []).append(key)

    by_lgu = {}
    for eid, lgu, report_date in events:
        by_lgu.setdefault(lgu, {})[eid] = {
            "report_date": report_date, "typhoon_keys": keys_by_event.get(eid, []), "records": [],
        }

    rows = db.session.execute(text(
        "SELECT re.relief_event_id, re.city_municipality, r.barangay_id, r.affected_families, "
        "r.affected_individuals, r.food_packs_given, r.total_families_snapshot, "
        "r.total_individuals_snapshot "
        "FROM barangay_relief_records r JOIN relief_events re ON re.relief_event_id = r.relief_event_id"
    )).fetchall()
    for eid, lgu, bid, fam, ind, packs, tf, ti in rows:
        by_lgu[lgu][eid]["records"].append({
            "barangay_id": bid, "affected_families": fam, "affected_individuals": ind,
            "food_packs_given": packs, "total_families_snapshot": tf, "total_individuals_snapshot": ti,
        })
    return by_lgu


def _as_date(value):
    """Coerce a raw SQL date value to a date object. This project's PyMySQL
    driver already returns datetime.date for DATE columns (verified against
    the live DB), but a raw text() query's return type isn't part of any
    contract - stay defensive rather than assume it holds under a different
    driver/config."""
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def load_typhoon_calendar():
    """[(typhoon_key, start_date, key_date, year)] - the verified 36-event
    calendar (scripts/typhoon_calendar_2021_2026.py)."""
    from sqlalchemy import text
    from app.extensions import db

    return db.session.execute(text(
        "SELECT typhoon_key, start_date, key_date, year FROM typhoon_calendar")).fetchall()


# ---------------------------------------------------------------------------
# Stage 1: barangay share of an LGU's relief for one typhoon
# ---------------------------------------------------------------------------

def _event_total_and_known(records):
    """(LGU total packs for this event, [records with a known food_packs_given]) -
    computed over only the barangays that reported a number; a barangay with
    no report for this event is excluded from both the total and the share
    fit, not silently counted as zero (see module doc - 'not reported' vs
    'confirmed zero' is preserved all the way from the real intake scripts)."""
    known = [r for r in records if r["food_packs_given"] is not None]
    total = sum(r["food_packs_given"] for r in known)
    return total, known


def _share_training_rows(events):
    """[(total_families_snapshot, share)] pooled across every event with at
    least 2 barangays reporting a known food_packs_given AND a known
    total_families_snapshot - the (X, y) pairs Stage 1 fits on."""
    rows = []
    for ev in events.values():
        total, known = _event_total_and_known(ev["records"])
        if total <= 0 or len(known) < 2:
            continue
        for r in known:
            if r["total_families_snapshot"] is not None:
                rows.append((r["total_families_snapshot"], r["food_packs_given"] / total))
    return rows


def fit_share_model(rows):
    """OLS share ~ total_families_snapshot on pooled (x, y) pairs. None if
    there isn't enough data to fit (fewer than 3 rows)."""
    if len(rows) < 3:
        return None
    x = np.array([r[0] for r in rows], dtype=float)
    y = np.array([r[1] for r in rows], dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    return {"slope": float(slope), "intercept": float(intercept), "n_rows": len(rows)}


def predict_shares(model, total_families_by_barangay):
    """{barangay_id: total_families} -> {barangay_id: share}, clipped >=0 and
    renormalized to sum to 1 (or split evenly if every prediction is <=0)."""
    raw = {bid: max(model["slope"] * tf + model["intercept"], 0.0)
           for bid, tf in total_families_by_barangay.items()}
    total = sum(raw.values())
    if total <= 0:
        n = len(raw) or 1
        return {bid: 1.0 / n for bid in raw}
    return {bid: v / total for bid, v in raw.items()}


def leave_one_typhoon_out_cv(events):
    """Refit Stage 1 excluding each event in turn, score the held-out event's
    barangay shares against: the model, an equal 1/N split, and each
    barangay's average share over the OTHER events. Returns per-baseline MAE,
    or None if there's too little data to run a single fold."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    err_model, err_equal, err_avg = [], [], []
    for held_out in scoreable:
        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        model = fit_share_model(_share_training_rows(train_events))
        if model is None:
            continue

        total, known = _event_total_and_known(events[held_out]["records"])
        actual_share = {r["barangay_id"]: r["food_packs_given"] / total for r in known}
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue  # can't fairly score a barangay the model has no predictor for
        pred_share = predict_shares(model, tf_map)

        hist_sum, hist_n = {}, {}
        for ev in train_events.values():
            t, k = _event_total_and_known(ev["records"])
            if t <= 0:
                continue
            for r in k:
                bid = r["barangay_id"]
                hist_sum[bid] = hist_sum.get(bid, 0.0) + r["food_packs_given"] / t
                hist_n[bid] = hist_n.get(bid, 0) + 1
        avg_raw = {bid: hist_sum[bid] / hist_n[bid] for bid in hist_sum}
        avg_total = sum(avg_raw.get(bid, 0.0) for bid in actual_share) or 1.0
        avg_share = {bid: avg_raw.get(bid, 0.0) / avg_total for bid in actual_share}

        n = len(actual_share)
        equal_share = {bid: 1.0 / n for bid in actual_share}

        for bid, a in actual_share.items():
            err_model.append(abs(a - pred_share.get(bid, 0.0)))
            err_equal.append(abs(a - equal_share[bid]))
            err_avg.append(abs(a - avg_share.get(bid, 0.0)))

    if not err_model:
        return None
    return {
        "mae_model": float(np.mean(err_model)),
        "mae_equal_split": float(np.mean(err_equal)),
        "mae_avg_share": float(np.mean(err_avg)),
        "n_folds": len(scoreable),
        "n_rows": len(err_model),
    }


# ---------------------------------------------------------------------------
# Stage 2: climatological frequency, P(relief), severity scenarios
# ---------------------------------------------------------------------------

def climatology_by_month(calendar_rows, today):
    """{month(1-12): expected typhoons in that calendar month} = (count of
    historical typhoons in that month) / (complete years observed for that
    month). A (year, month) is 'complete' only once that month has fully
    ended relative to `today` - e.g. run in Sep 2026, Jan-Aug 2026 count but
    Sep-Dec 2026 don't yet, so those months fall back to 2021-2025 only."""
    from collections import defaultdict

    counts = defaultdict(int)
    for _key, start, key_date, _year in calendar_rows:
        d = _as_date(key_date) or _as_date(start)
        counts[d.month] += 1
    years = sorted({row[3] for row in calendar_rows})
    if not years:
        return {m: 0.0 for m in range(1, 13)}
    min_year, max_year = years[0], years[-1]

    rate = {}
    for m in range(1, 13):
        complete = sum(1 for y in range(min_year, max_year + 1)
                        if y < today.year or (y == today.year and m < today.month))
        rate[m] = counts[m] / complete if complete > 0 else 0.0
    return rate


def p_relief(events, all_typhoon_keys):
    """Fraction of the calendar's 36 typhoons that have at least one real
    relief record for this LGU - deliberately NOT typhoon_calendar's
    pangasinan_impact_confirmed column (see module doc)."""
    covered = set()
    for ev in events.values():
        covered.update(ev["typhoon_keys"])
    universe = set(all_typhoon_keys)
    return len(covered & universe) / len(universe) if universe else 0.0


def severity_scenarios(events):
    """25th percentile (low) / mean (expected) / 90th percentile (high) of
    this LGU's real per-typhoon totals (only events with >=1 barangay
    reporting a known food_packs_given)."""
    totals = [t for ev in events.values() if (t := _event_total_and_known(ev["records"])[0]) > 0]
    if not totals:
        return {"low": 0.0, "expected": 0.0, "high": 0.0, "n": 0}
    arr = np.array(totals, dtype=float)
    return {
        "low": float(np.percentile(arr, 25)),
        "expected": float(arr.mean()),
        "high": float(np.percentile(arr, 90)),
        "n": len(totals),
    }


def _loto_severity_excluding(events, exclude_eid):
    """severity_scenarios computed with one event left out - used only to
    build an honest (non-leaking) backtest point for that event."""
    totals = [t for eid, ev in events.items() if eid != exclude_eid
              and (t := _event_total_and_known(ev["records"])[0]) > 0]
    if not totals:
        return None
    arr = np.array(totals, dtype=float)
    return {"expected": float(arr.mean()), "high": float(np.percentile(arr, 90))}


def _backtest_points(events, calendar_by_key):
    """One point per event with a known LGU total: the real total vs. what
    the severity scenarios would have said with that event excluded (the
    leave-one-typhoon-out analogue of the old rolling-origin backtest chart -
    see app.ml.predict.backtest_series and app.ml.charts.backtest_chart)."""
    points = []
    for eid, ev in events.items():
        total, known = _event_total_and_known(ev["records"])
        if total <= 0 or not known:
            continue
        sev = _loto_severity_excluding(events, eid)
        if sev is None:
            continue
        month = _as_date(ev["report_date"])
        if month is None and ev["typhoon_keys"]:
            cal = calendar_by_key.get(ev["typhoon_keys"][0])
            month = _as_date(cal[0]) if cal else None
        if month is None:
            continue
        points.append({"date": month, "actual": total, "expected": sev["expected"], "p90": sev["high"]})
    points.sort(key=lambda p: p["date"])
    return points


def leave_one_typhoon_out_packs_cv(events):
    """Leave-one-typhoon-out validation of the FULL pipeline's pack-count
    predictions - predicted_packs(barangay) = that fold's LOTO severity.expected
    x that fold's LOTO share (both refit excluding the held-out event) -
    against real food_packs_given, pooled over every (barangay, held-out
    typhoon) pair. Unlike leave_one_typhoon_out_cv (which scores the share
    model alone, in proportions), this scores the end-to-end forecast a user
    actually sees, in packs. None if there isn't enough data to run a single
    fold.

    MAE/RMSE only (no MAPE/R2, tried and dropped 2026-09-28): a single
    typhoon's severity is inherently volatile and not meant to be point-
    forecast exactly (that's what the P90 scenario range is for, not a single
    number) - MAPE exploded past 1,000% on intermittent near-zero actuals and
    R2 sat near/below 0, both technically correct but not informative without
    a longer explanation than a dashboard tile can carry. MAE/RMSE in packs
    still say something useful (typical/worst-case miss size) without that
    baggage."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    actual, predicted = [], []
    for held_out in scoreable:
        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        model = fit_share_model(_share_training_rows(train_events))
        sev = _loto_severity_excluding(events, held_out)
        if model is None or sev is None:
            continue

        _total, known = _event_total_and_known(events[held_out]["records"])
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue
        pred_share = predict_shares(model, tf_map)

        for r in known:
            actual.append(r["food_packs_given"])
            predicted.append(sev["expected"] * pred_share.get(r["barangay_id"], 0.0))

    if not actual:
        return None

    a, p = np.array(actual, dtype=float), np.array(predicted, dtype=float)
    err = a - p
    return {
        "mae_packs": float(np.abs(err).mean()),
        "rmse_packs": float(np.sqrt((err ** 2).mean())),
        "n": len(a),
    }


def leave_one_typhoon_out_p90_coverage(events):
    """Leave-one-typhoon-out check of the P90 promise itself: does the
    recommended stockpile (that fold's LOTO severity.high) actually cover
    what really happened, at the rate it's supposed to (~90%)? Unlike
    MAE/RMSE (how far off a point estimate is), this scores the thing the
    P90 level is actually FOR - not running out - so it's meaningful even
    though a single typhoon's exact size can't be point-forecast (see
    leave_one_typhoon_out_packs_cv's docstring).

    Two levels, both leave-one-typhoon-out, no (1 + BUFFER) applied (that's
    a deployment-time safety margin on top of raw P90, so live coverage
    should run a bit higher than what's reported here):
      lgu_coverage     - held-out event's real LGU total <= that fold's P90
                          LGU total.
      barangay_coverage - same check per barangay (share x P90 total vs
                          real food_packs_given), pooled across all
                          (barangay, held-out typhoon) pairs.
    None if there isn't enough data to run a single fold."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    lgu_hits = lgu_n = brgy_hits = brgy_n = 0
    for held_out in scoreable:
        sev = _loto_severity_excluding(events, held_out)
        if sev is None:
            continue
        total, known = _event_total_and_known(events[held_out]["records"])

        lgu_hits += int(total <= sev["high"])
        lgu_n += 1

        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        model = fit_share_model(_share_training_rows(train_events))
        if model is None:
            continue
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue
        pred_share = predict_shares(model, tf_map)
        for r in known:
            p90_packs = sev["high"] * pred_share.get(r["barangay_id"], 0.0)
            brgy_hits += int(r["food_packs_given"] <= p90_packs)
            brgy_n += 1

    if lgu_n == 0 or brgy_n == 0:
        return None
    return {
        "lgu_coverage": lgu_hits / lgu_n,
        "barangay_coverage": brgy_hits / brgy_n,
        "lgu_n": lgu_n,
        "barangay_n": brgy_n,
    }


# ---------------------------------------------------------------------------
# Train + persist
# ---------------------------------------------------------------------------

def train_and_persist():
    """Fits Stage 1 (share regression) and computes Stage 2 (climatology,
    P(relief), severity scenarios) for every LGU with real relief data, runs
    leave-one-typhoon-out validation, saves the artifact for app.ml.predict,
    and records ModelMetrics."""
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    by_lgu = load_relief_data()
    if not by_lgu:
        raise RuntimeError(
            "No relief_events found. Run scripts/apply_relief_schema.py, "
            "scripts/typhoon_calendar_2021_2026.py then scripts/load_relief_events.py first."
        )

    calendar_rows = load_typhoon_calendar()
    all_keys = [r[0] for r in calendar_rows]
    calendar_by_key = {r[0]: (r[1], r[2], r[3]) for r in calendar_rows}
    climatology = climatology_by_month(calendar_rows, ph_today())

    lgu_artifact, loto_cv, loto_packs_cv, loto_p90, backtest_series = {}, {}, {}, {}, {}
    for lgu, events in by_lgu.items():
        rows = _share_training_rows(events)
        model = fit_share_model(rows)
        if model is None:
            continue

        # Sort events chronologically first so the LAST write per barangay is
        # actually the most recent snapshot - load_relief_data()'s query has
        # no ORDER BY, so events.values() iterates in whatever order the DB
        # happened to return rows, not report_date order (found in review,
        # 2026-09-28: this directly fed share_breakdown()'s "family count
        # used" for current forecasting, so a wrong "latest" silently skewed
        # shares).
        latest_tf = {}
        for ev in sorted(events.values(), key=lambda e: _as_date(e["report_date"]) or date.min):
            for r in ev["records"]:
                if r["total_families_snapshot"] is not None:
                    latest_tf[r["barangay_id"]] = r["total_families_snapshot"]

        lgu_artifact[lgu] = {
            "share_model": model,
            "p_relief": p_relief(events, all_keys),
            "severity": severity_scenarios(events),
            "barangays": {bid: {"latest_total_families": tf} for bid, tf in latest_tf.items()},
        }
        loto_cv[lgu] = leave_one_typhoon_out_cv(events)
        loto_packs_cv[lgu] = leave_one_typhoon_out_packs_cv(events)
        loto_p90[lgu] = leave_one_typhoon_out_p90_coverage(events)
        backtest_series[lgu] = {
            "origin": "leave-one-typhoon-out",
            "points": [
                {"month": p["date"].strftime("%Y-%m"),  # _backtest_points guarantees a real date via _as_date
                 "actual": p["actual"], "expected": p["expected"], "p90": p["p90"]}
                for p in _backtest_points(events, calendar_by_key)
            ],
        }

    if not lgu_artifact:
        raise RuntimeError("Not enough real relief data to fit a share model for any LGU.")

    data_through = ph_today().isoformat()
    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    joblib.dump({
        "version": MODEL_VERSION,
        "trained_at": ph_now().isoformat(),
        "data_through": data_through,
        "buffer": BUFFER,
        "climatology": climatology,
        "lgu": lgu_artifact,
        "loto_cv": loto_cv,
        "loto_packs_cv": loto_packs_cv,
        "loto_p90": loto_p90,
        "backtest_series": backtest_series,
    }, ARTIFACT_PATH)

    scored = {lgu: cv for lgu, cv in loto_cv.items() if cv}
    packs_scored = {lgu: cv for lgu, cv in loto_packs_cv.items() if cv}
    p90_scored = {lgu: cv for lgu, cv in loto_p90.items() if cv}
    if scored:
        # p90_coverage "worst LGU" = LOWEST coverage (min), unlike the error
        # metrics above where worst = highest (max) - a lower coverage rate
        # is the bad direction here, not a higher one.
        db.session.add(ModelMetrics(
            model_version=MODEL_VERSION,
            mae=round(max(cv["mae_model"] for cv in scored.values()), 4),
            mae_baseline_equal_split=round(max(cv["mae_equal_split"] for cv in scored.values()), 4),
            mae_baseline_avg_share=round(max(cv["mae_avg_share"] for cv in scored.values()), 4),
            mae_packs=round(max(cv["mae_packs"] for cv in packs_scored.values()), 4) if packs_scored else None,
            rmse=round(max(cv["rmse_packs"] for cv in packs_scored.values()), 4) if packs_scored else None,
            p90_coverage=round(min(cv["barangay_coverage"] for cv in p90_scored.values()), 4) if p90_scored else None,
            training_samples=sum(len(ev["records"]) for events in by_lgu.values() for ev in events.values()),
        ))
        db.session.commit()

    return {"lgus": list(lgu_artifact), "loto_cv": loto_cv, "loto_packs_cv": loto_packs_cv,
            "loto_p90": loto_p90, "data_through": data_through}
