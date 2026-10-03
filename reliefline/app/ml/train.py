"""
Trains the food-pack TWO-STAGE forecaster: per LGU (Urdaneta City, Santa
Barbara, Calasiao), Stage 1 predicts each barangay's SHARE of its LGU's
relief for a typhoon (a size-weighted family-count regression blended with
the barangay's own relief history, with a per-family floor - see v9.2
below), and Stage 2 is computed
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
  regressed on total_families_snapshot, each row weighted by its event's
  LGU total (v9.1 - see fit_share_model) (the ONLY predictor - a barangay's
  own affected_families/food_packs_given for a FUTURE typhoon obviously
  can't be a predictor of themselves, and adding total_individuals_snapshot
  alongside total_families_snapshot was tested informally and added nothing,
  since the two are collinear).

  Stage 2 (severity/frequency, computed): how bad is a typical typhoon for
  this LGU, and how often does one hit? Both come straight from real
  records/the verified calendar, not a fitted model - with 8-14 events per
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
  the same as relief not happening). It is relief EVENTS per calendar
  typhoon (v9.3 fix - counting storms covered overstated totals by up to
  x1.38, since one combined report can cover several storms), and a LOWER
  bound, since a storm with no record is treated as no relief.

  v9.1 (2026-10-03): the regression is weighted by each event's LGU total.
  v9.2 (2026-10-03): the regression share is BLENDED with each barangay's
  pooled relief history (share = alpha x history + (1 - alpha) x
  regression, alpha tuned per LGU by leave-one-typhoon-out, capped at 0.75)
  and FLOORED at SHARE_FLOOR x its per-family share, so a barangay with
  little relief history still gets stock - see fit_stage1, predict_shares,
  apply_share_floor.
  v9.3 (2026-10-03): P(relief) fix above.

Formula (see app.ml.predict.forecast_lgu for the actual implementation):
  stock(barangay, horizon, scenario) =
      expected_typhoons(horizon) x P(relief) x total_packs(scenario)
      x share(barangay) x (1 + BUFFER)
Known limits: the horizon P90 is expected storms x P(relief) x the per-event
P90, not the P90 of a multi-storm total (not a safety stock under ~6
months), and no forecast built from 8-14 events covers a once-in-years storm
(Calasiao's 39,103-pack Crising + Emong exceeds its 12-month P90).

Validation: leave-one-typhoon-out cross-validation (leave_one_typhoon_out_cv)
against three baselines - equal 1/N split, each barangay's average
per-event share, and POOLED HISTORY (its share of all past relief, the
strongest) - refit on every OTHER event, scored on the held-out one, plain
and size-weighted, with "beats pooled history in k of n storms" and a
bootstrap interval. As of v9.3 the model does NOT clearly beat pooled
history in any LGU (every interval crosses 0): its case is protecting
barangays with little relief history (cap + floor), not proven accuracy.
With 7-14 scored storms per LGU and the design choices made on the same
data, treat every figure as approximate.
--------------------------------------------------------------------------
"""
import os
import statistics
from datetime import date

from app.utils.timezone import ph_now, ph_today

import numpy as np
import joblib

MODEL_VERSION = "v9.3-two-stage-lgu"
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
    """[(total_families_snapshot, share, event_total)] pooled across every
    event with at least 2 barangays reporting a known food_packs_given AND a
    known total_families_snapshot - the (X, y) pairs Stage 1 fits on, plus
    the event's LGU total packs as the row's fitting weight."""
    rows = []
    for ev in events.values():
        total, known = _event_total_and_known(ev["records"])
        if total <= 0 or len(known) < 2:
            continue
        for r in known:
            if r["total_families_snapshot"] is not None:
                rows.append((r["total_families_snapshot"], r["food_packs_given"] / total, total))
    return rows


def fit_share_model(rows):
    """Weighted least squares share ~ total_families_snapshot on pooled
    (x, y, event_total) rows, each row weighted by its event's LGU total
    packs. None if there isn't enough data to fit (fewer than 3 rows).

    Why weighted (v9.1, 2026-10-03): unweighted, a 1-pack storm (one barangay
    gets share 1.0, the rest 0) pulled the line as hard as a 39,000-pack one,
    though its shares say almost nothing about where relief goes in a real
    operation. Weighting by size keeps every event but lets the big
    operations the stockpile is actually for dominate the fit. Chosen over a
    minimum-size cut-off (which performed about the same in a fixed-test-set
    comparison) because it needs no arbitrary threshold."""
    if len(rows) < 3:
        return None
    x = np.array([r[0] for r in rows], dtype=float)
    y = np.array([r[1] for r in rows], dtype=float)
    # np.polyfit's w multiplies the residuals, so sqrt(weight) gives a
    # squared-error weight of exactly event_total.
    w = np.sqrt(np.array([r[2] for r in rows], dtype=float))
    slope, intercept = np.polyfit(x, y, 1, w=w)
    return {"slope": float(slope), "intercept": float(intercept), "n_rows": len(rows),
            "weighting": "event_total"}


def predict_shares(model, total_families_by_barangay, history=None, alpha=0.0, floor=0.0):
    """{barangay_id: total_families} -> {barangay_id: share}, summing to 1.

    1. Regression: clip(slope x total_families + intercept, 0), renormalized
       (split evenly if every prediction is <= 0).
    2. History blend (v9.2): alpha x the barangay's pooled relief history
       (see pooled_history_shares, renormalized over these barangays) +
       (1 - alpha) x its regression share. A barangay with no relief record
       at all keeps its regression share.
    3. Floor (v9.2): no barangay ends below `floor` x its per-family share
       (families / LGU families) - see apply_share_floor.
    With the defaults (no history, alpha 0, floor 0) this is the plain
    regression split."""
    raw = {bid: max(model["slope"] * tf + model["intercept"], 0.0)
           for bid, tf in total_families_by_barangay.items()}
    total = sum(raw.values())
    if total <= 0:
        n = len(raw) or 1
        shares = {bid: 1.0 / n for bid in raw}
    else:
        shares = {bid: v / total for bid, v in raw.items()}

    if history and alpha > 0:
        have = {bid: history[bid] for bid in shares if history.get(bid) is not None}
        hsum = sum(have.values())
        if hsum > 0:
            shares = {bid: (alpha * have[bid] / hsum + (1 - alpha) * s) if bid in have else s
                      for bid, s in shares.items()}
            ssum = sum(shares.values())
            shares = {bid: s / ssum for bid, s in shares.items()}

    return apply_share_floor(shares, total_families_by_barangay, floor)


def apply_share_floor(shares, total_families_by_barangay, floor):
    """Lift every barangay below `floor` x (its families / the LGU's families)
    up to that minimum, and scale the rest down to make room so shares still
    sum to 1. Repeats until no scaled-down barangay falls under its own
    minimum. No-op if floor <= 0 or family counts are unknown.

    Why (v9.2, 2026-10-03): a barangay with little relief history - or a
    small one the regression line clips to ~0 (Calasiao's Poblacion West got
    a 0.0001 share under v9.1) - can still need relief in the next storm.
    The floor guarantees every barangay keeps at least part of what its
    population alone would justify."""
    ftot = sum(tf for tf in total_families_by_barangay.values() if tf)
    if floor <= 0 or ftot <= 0:
        return shares
    minimum = {bid: floor * (total_families_by_barangay.get(bid) or 0) / ftot for bid in shares}
    fixed = {}
    while True:
        free = {bid: s for bid, s in shares.items() if bid not in fixed}
        if not free:
            return fixed
        room = 1.0 - sum(fixed.values())
        fsum = sum(free.values())
        scaled = ({bid: s * room / fsum for bid, s in free.items()} if fsum > 0
                  else {bid: room / len(free) for bid in free})
        below = {bid: minimum[bid] for bid, s in scaled.items() if s < minimum[bid]}
        if not below:
            return {**fixed, **scaled}
        fixed.update(below)


def _is_supply_only(known):
    """True for an event where no reported barangay has a family snapshot -
    a supply-distribution sheet (e.g. Sta. Barbara's Aug 2026 DSWD+LGU
    sheet), not a needs report. Excluded from every history-based share
    (model and baselines alike) but kept in Stage 2 severity."""
    return not any(r["total_families_snapshot"] is not None for r in known)


def pooled_history_shares(events):
    """{barangay_id: share of the LGU's relief it has historically received}
    = sum of its food_packs_given / sum of those events' LGU totals, over
    every event it reported in. Pooling (rather than averaging per-event
    shares) weights each event by its size, matching fit_share_model - a
    1-pack storm barely moves it.

    Events with no family snapshot on any record are skipped: those are
    supply-distribution sheets (e.g. Sta. Barbara's Aug 2026 DSWD+LGU sheet),
    which record where packs were sent, not where need was reported, and
    can never be held out in validation since they have no family counts.
    They still count toward Stage 2 severity (a real operation's size)."""
    num, den = {}, {}
    for ev in events.values():
        total, known = _event_total_and_known(ev["records"])
        if total <= 0 or _is_supply_only(known):
            continue
        for r in known:
            bid = r["barangay_id"]
            num[bid] = num.get(bid, 0.0) + r["food_packs_given"]
            den[bid] = den.get(bid, 0.0) + total
    return {bid: num[bid] / den[bid] for bid in num}


# Blend weights tried for the history blend, and the per-family floor.
# Chosen from a fixed-test-set comparison on 2026-10-03 (see
# fit_stage1's docstring): a floor of 0.5 cost almost no accuracy.
# alpha is capped at 0.75 on purpose: history never decides a share alone,
# so at least a quarter of every barangay's share always comes from its
# family count - a barangay that happened to get little relief in past
# storms can still need it in the next one. (Sta. Barbara's tuning picked
# 1.0 when allowed, but 0.75 scored the same: 0.0110 vs 0.0111.)
ALPHA_GRID = (0.0, 0.25, 0.5, 0.75)
SHARE_FLOOR = 0.5

_STAGE1_CACHE = {}


def _scoreable_with_families(events):
    out = []
    for eid, ev in events.items():
        total, known = _event_total_and_known(ev["records"])
        if total > 0 and len(known) >= 2 and all(r["total_families_snapshot"] is not None for r in known):
            out.append(eid)
    return out


def _weighted_share_error(events, alpha):
    """Size-weighted LOTO share MAE of the blend at a fixed alpha, over
    `events` only - used to tune alpha without ever looking at the event
    being scored by the outer validation."""
    errs, weights = [], []
    for held_out in _scoreable_with_families(events):
        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        model = fit_share_model(_share_training_rows(train_events))
        if model is None:
            continue
        total, known = _event_total_and_known(events[held_out]["records"])
        tf = {r["barangay_id"]: r["total_families_snapshot"] for r in known}
        pred = predict_shares(model, tf, pooled_history_shares(train_events), alpha, SHARE_FLOOR)
        for r in known:
            errs.append(abs(r["food_packs_given"] / total - pred[r["barangay_id"]]))
            weights.append(total)
    return float(np.average(errs, weights=weights)) if errs else None


def fit_stage1(events):
    """Stage 1 for one LGU's events: the weighted share regression, every
    barangay's pooled relief history, and the blend weight alpha - picked
    from ALPHA_GRID by the lowest size-weighted leave-one-typhoon-out share
    error over these same events (ties -> the smaller alpha, i.e. leaning on
    population). None if the regression can't be fit.

    Memoized per set of event ids, since the three LOTO validations below
    all refit the same folds.

    Why blend history in (v9.2, 2026-10-03): family count alone explains
    only part of where relief goes - some barangays flood every storm. The
    blend clearly helped Sta. Barbara over the family-count regression alone
    and was about neutral elsewhere, but it does NOT clearly beat pooled
    history alone in any LGU (see leave_one_typhoon_out_cv's k-of-n and
    bootstrap interval) - run scripts/train_model.py for the current
    figures rather than trusting numbers quoted here."""
    key = frozenset(events)
    if key in _STAGE1_CACHE:
        return _STAGE1_CACHE[key]
    model = fit_share_model(_share_training_rows(events))
    result = None
    if model is not None:
        best_alpha, best_err = 0.0, None
        if len(_scoreable_with_families(events)) >= 2:
            for alpha in ALPHA_GRID:
                err = _weighted_share_error(events, alpha)
                if err is not None and (best_err is None or err < best_err):
                    best_alpha, best_err = alpha, err
        result = {"model": model, "history": pooled_history_shares(events), "alpha": best_alpha}
    _STAGE1_CACHE[key] = result
    return result


def stage1_shares(stage1, total_families_by_barangay):
    """Shares from a fit_stage1() result (regression + history blend + floor)."""
    return predict_shares(stage1["model"], total_families_by_barangay,
                          stage1["history"], stage1["alpha"], SHARE_FLOOR)


def leave_one_typhoon_out_cv(events):
    """Refit Stage 1 excluding each event in turn, score the held-out event's
    barangay shares against: the model, an equal 1/N split, and each
    barangay's average share over the OTHER events. Returns per-baseline MAE,
    or None if there's too little data to run a single fold.

    Two scores per method, on the SAME held-out rows:
      mae_*          - plain mean over every (event, barangay) pair, so a
                       1-pack storm counts as much as a 39,000-pack one;
      mae_*_weighted - each pair weighted by its event's LGU total, i.e. how
                       much relief actually lands in the wrong barangay.
    Near-empty storms (a few packs to 1-3 barangays) are unpredictable by
    any method and dominate the plain score; the weighted one reflects real
    misallocation. Both are reported - neither replaces the other.

    Also scored against POOLED HISTORY alone (pooled_history_shares - the
    same size-weighted history the model blends in), the strongest simple
    baseline: avg-share averages per-event shares, so a 1-pack storm counts
    as much as a 39,000-pack one, which makes it easy to beat. With only
    8-14 events per LGU, a third-decimal MAE difference isn't evidence, so
    the comparison with pooled history is also given as "model beats it in
    k of n held-out storms" (size-weighted error per storm) and a bootstrap
    95% interval (resampling held-out storms) for the size-weighted MAE
    difference, model minus pooled history - negative = model better. Expect
    it to be wide."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    err_model, err_equal, err_avg, err_pooled, weights = [], [], [], [], []
    per_event = []  # (event total, sum |err| model, sum |err| pooled history, n barangays)
    for held_out in scoreable:
        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        stage1 = fit_stage1(train_events)
        if stage1 is None:
            continue

        total, known = _event_total_and_known(events[held_out]["records"])
        actual_share = {r["barangay_id"]: r["food_packs_given"] / total for r in known}
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue  # can't fairly score a barangay the model has no predictor for
        pred_share = stage1_shares(stage1, tf_map)

        hist_sum, hist_n = {}, {}
        for ev in train_events.values():
            t, k = _event_total_and_known(ev["records"])
            if t <= 0 or _is_supply_only(k):
                continue
            for r in k:
                bid = r["barangay_id"]
                hist_sum[bid] = hist_sum.get(bid, 0.0) + r["food_packs_given"] / t
                hist_n[bid] = hist_n.get(bid, 0) + 1
        avg_raw = {bid: hist_sum[bid] / hist_n[bid] for bid in hist_sum}
        avg_total = sum(avg_raw.get(bid, 0.0) for bid in actual_share) or 1.0
        avg_share = {bid: avg_raw.get(bid, 0.0) / avg_total for bid in actual_share}

        pooled_raw = pooled_history_shares(train_events)
        pooled_total = sum(pooled_raw.get(bid, 0.0) for bid in actual_share) or 1.0
        pooled_share = {bid: pooled_raw.get(bid, 0.0) / pooled_total for bid in actual_share}

        n = len(actual_share)
        equal_share = {bid: 1.0 / n for bid in actual_share}

        s_model = s_pooled = 0.0
        for bid, a in actual_share.items():
            e_m = abs(a - pred_share.get(bid, 0.0))
            e_p = abs(a - pooled_share[bid])
            err_model.append(e_m)
            err_equal.append(abs(a - equal_share[bid]))
            err_avg.append(abs(a - avg_share.get(bid, 0.0)))
            err_pooled.append(e_p)
            weights.append(total)
            s_model += e_m
            s_pooled += e_p
        per_event.append((total, s_model, s_pooled, n))

    if not err_model:
        return None

    # k of n: held-out storms where the model's share error beats pooled
    # history's (ties - e.g. both perfect - count as not beating).
    beats_k = sum(1 for _t, sm, sp, _n in per_event if sm < sp)
    # Bootstrap the size-weighted MAE difference over held-out storms.
    pe = np.array(per_event, dtype=float)
    rng = np.random.default_rng(0)
    diffs = []
    for _ in range(2000):
        s = pe[rng.integers(0, len(pe), len(pe))]
        denom = (s[:, 0] * s[:, 3]).sum()
        diffs.append(((s[:, 0] * s[:, 1]).sum() - (s[:, 0] * s[:, 2]).sum()) / denom)
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
    return {
        "mae_pooled_history": float(np.mean(err_pooled)),
        "mae_pooled_history_weighted": float(np.average(err_pooled, weights=weights)),
        "beats_pooled_k": beats_k,
        "beats_pooled_n": len(per_event),
        "diff_vs_pooled_weighted_ci": (float(ci_low), float(ci_high)),
        "mae_model": float(np.mean(err_model)),
        "mae_equal_split": float(np.mean(err_equal)),
        "mae_avg_share": float(np.mean(err_avg)),
        "mae_model_weighted": float(np.average(err_model, weights=weights)),
        "mae_equal_split_weighted": float(np.average(err_equal, weights=weights)),
        "mae_avg_share_weighted": float(np.average(err_avg, weights=weights)),
        # Storms actually scored - a supply-only event (no family counts)
        # can't be, so this can be smaller than the LGU's event count.
        "n_folds": len(per_event),
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
    """Relief operations per calendar typhoon for this LGU: the number of
    real relief EVENTS with packs (linked to at least one calendar typhoon)
    divided by the calendar's typhoon count - deliberately NOT
    typhoon_calendar's pangasinan_impact_confirmed column (see module doc).

    Fixed 2026-10-03 (was: calendar typhoons COVERED by a relief record /
    36). The forecast multiplies this by severity, which is the mean size of
    a relief EVENT, and a combined report (e.g. Urdaneta's "Nika + Ofel +
    Pepito") is one event covering several storms - counting storms covered
    overstated historical totals by x1.36 (Urdaneta), x1.38 (Sta. Barbara)
    and x1.07 (Calasiao). A leave-one-year-out check put the new definition
    closer to the actual yearly total in 14 of 18 LGU-years; it fixes the
    bias in typical years and says nothing about 2025-type years, which no
    version predicts.

    Caveat: a storm with no relief record is counted as no relief, but some
    may simply not have been digitized - so this is a LOWER bound on how
    often relief happens."""
    universe = set(all_typhoon_keys)
    if not universe:
        return 0.0
    n_events = sum(1 for ev in events.values()
                   if set(ev["typhoon_keys"]) & universe and _event_total_and_known(ev["records"])[0] > 0)
    return n_events / len(universe)


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
        "max": float(arr.max()),  # largest real event, for the "P90 below worst storm" warning
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
        stage1 = fit_stage1(train_events)
        sev = _loto_severity_excluding(events, held_out)
        if stage1 is None or sev is None:
            continue

        _total, known = _event_total_and_known(events[held_out]["records"])
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue
        pred_share = stage1_shares(stage1, tf_map)

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
      barangay_coverage_nonzero - the same, only over pairs where the
                          barangay actually received packs. A barangay that
                          got 0 is trivially "covered", and most pairs in
                          small storms are 0, so barangay_coverage alone
                          flatters the model - judge P90 by lgu_coverage and
                          this one.
    lgu_n counts every event with packs, including a supply-only sheet (a
    real LGU total - Sta. Barbara's event 49); the barangay-level figures
    skip it, since it has no family counts to split by. So the two levels
    can be over different storm counts.
    None if there isn't enough data to run a single fold."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    lgu_hits = lgu_n = brgy_hits = brgy_n = nz_hits = nz_n = 0
    for held_out in scoreable:
        sev = _loto_severity_excluding(events, held_out)
        if sev is None:
            continue
        total, known = _event_total_and_known(events[held_out]["records"])

        lgu_hits += int(total <= sev["high"])  # every event with packs, supply-only included
        lgu_n += 1

        train_events = {eid: ev for eid, ev in events.items() if eid != held_out}
        stage1 = fit_stage1(train_events)
        if stage1 is None:
            continue
        tf_map = {r["barangay_id"]: r["total_families_snapshot"] for r in known
                  if r["total_families_snapshot"] is not None}
        if len(tf_map) < len(known):
            continue
        pred_share = stage1_shares(stage1, tf_map)
        for r in known:
            p90_packs = sev["high"] * pred_share.get(r["barangay_id"], 0.0)
            hit = int(r["food_packs_given"] <= p90_packs)
            brgy_hits += hit
            brgy_n += 1
            if r["food_packs_given"] > 0:
                nz_hits += hit
                nz_n += 1

    if lgu_n == 0 or brgy_n == 0:
        return None
    return {
        "lgu_coverage": lgu_hits / lgu_n,
        "lgu_hits": lgu_hits,
        "barangay_coverage": brgy_hits / brgy_n,
        "barangay_nonzero_hits": nz_hits,
        "lgu_n": lgu_n,
        "barangay_n": brgy_n,
        "barangay_coverage_nonzero": nz_hits / nz_n if nz_n else None,
        "barangay_nonzero_n": nz_n,
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

    _STAGE1_CACHE.clear()
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
        stage1 = fit_stage1(events)
        if stage1 is None:
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
            "share_model": stage1["model"],
            "history_share": stage1["history"],
            "alpha": stage1["alpha"],
            "share_floor": SHARE_FLOOR,
            "p_relief": p_relief(events, all_keys),
            "severity": severity_scenarios(events),
            "barangays": {bid: {"latest_total_families": tf} for bid, tf in latest_tf.items()},
            # What this LGU was trained on - check_forecast compares these
            # with the database to catch a model older than the data.
            "event_ids": sorted(events),
            "n_events_with_packs": sum(1 for ev in events.values()
                                       if _event_total_and_known(ev["records"])[0] > 0),
            # Record count and total packs too, so an edit INSIDE an
            # existing event (same ids) still shows the model as stale.
            "n_records": sum(len(ev["records"]) for ev in events.values()),
            "total_packs": sum(_event_total_and_known(ev["records"])[0] for ev in events.values()),
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
            # Worst LGU's P90 coverage over barangays that actually received
            # packs - the plain barangay figure is inflated by 0-pack rows.
            p90_coverage=round(min(cv["barangay_coverage_nonzero"] for cv in p90_scored.values()
                                   if cv.get("barangay_coverage_nonzero") is not None), 4) if p90_scored else None,
            training_samples=sum(len(ev["records"]) for events in by_lgu.values() for ev in events.values()),
        ))
        db.session.commit()

    return {"lgus": list(lgu_artifact), "loto_cv": loto_cv, "loto_packs_cv": loto_packs_cv,
            "loto_p90": loto_p90, "data_through": data_through}
