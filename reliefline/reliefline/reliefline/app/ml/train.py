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
  records/the typhoon calendar, not a fitted model - with 8-14 events per
  LGU there isn't enough data to fit a distribution shape, so empirical
  percentiles (25th/mean/90th of real per-typhoon LGU totals) and a simple
  frequency count are the honest choice. Crucially, frequency is CLIMATOLOGICAL
  (how many typhoons has this calendar month historically had, from
  typhoon_calendar - a fact independent of any future storm's existence) so a
  forecast for "next 3 months" run in December can climatologically show ~0
  expected typhoons (Dec-May has none in the record) without needing to
  predict an unknowable future event - see app.ml.predict._forecast_window.
  Since 2026-10-03 the calendar is built ONLY from the relief reports: every
  storm a report names, dated by the reports
  (scripts/typhoon_calendar_from_reports.py). The earlier researched
  36-storm list was removed on request.

  P(relief) - relief operations for THIS LGU per calendar storm - is
  computed from real relief-record coverage (p_relief below). It is relief
  EVENTS per calendar typhoon (v9.3 fix - counting storms covered overstated
  totals by up to x1.38, since one combined report can cover several
  storms). With the calendar built from the reports, a storm only counts if
  some LGU reported relief for it, so this is "relief events per REPORTED
  storm"; storms x P(relief) still reproduces each LGU's real event count.

  v9.1 (2026-10-03): the regression is weighted by each event's LGU total.
  v9.2 (2026-10-03): the regression share is BLENDED with each barangay's
  pooled relief history (share = alpha x history + (1 - alpha) x
  regression, alpha tuned per LGU by leave-one-typhoon-out, capped at 0.75)
  and FLOORED at SHARE_FLOOR x its per-family share, so a barangay with
  little relief history still gets stock - see fit_stage1, predict_shares,
  apply_share_floor.
  v9.3 (2026-10-03): P(relief) fix above.

Formula (see app.ml.predict.forecast_lgu for the actual implementation):
  expected(barangay, horizon)  = expected_typhoons(horizon) x P(relief)
                                 x mean event size x share(barangay)
  stockpile(barangay, horizon) = expected_typhoons(horizon) x P(relief)
                                 x per-event P90 x share(barangay)
                                 x (1 + BUFFER)
The buffer applies to the stockpile only (2026-10-03). Known limits: the
stockpile is expected storms x the per-STORM P90, not a true percentile of
a multi-storm (e.g. yearly) total; it is compared on the page with the
largest single storm AND the largest year on record (yearly_totals). No
forecast built from 8-14 events is guaranteed to cover a once-in-years
storm or season (2025 was one).

Validation: leave-one-typhoon-out cross-validation (leave_one_typhoon_out_cv)
against three baselines - equal 1/N split, each barangay's average
per-event share, and POOLED HISTORY (its share of all past relief, the
strongest) - refit on every OTHER event, scored on the held-out one, plain
and size-weighted, with "beats pooled history in k of n storms" and a
bootstrap interval. As of v9.3 the model does NOT clearly beat pooled
history in any LGU: Calasiao's and Urdaneta's intervals cross 0, and on
Sta. Barbara's full 14-report set (2026-10-03) pooled history is slightly
but measurably better (size-weighted 0.0108 vs 0.0116, interval +0.0001 to
+0.0015) - the price of the 50% floor and the 0.75 alpha cap, which move
share toward barangays with little relief history. That protection is the
model's case, not proven accuracy.
With 7-14 scored storms per LGU and the design choices made on the same
data, treat every figure as approximate.

Experiment log - tried on the same leave-one-typhoon-out data, kept or
rejected (adopt only if it beats the current model on the same metrics):
  ADOPTED  v9.1 size-weighted share regression (2026-10-03).
  ADOPTED  v9.2 history blend + 50% floor (ties pooled history; kept for
           the floor's protection of barangays with little history).
  ADOPTED  v9.3 P(relief) = relief events / calendar storms.
  ADOPTED  buffer on the stockpile only (2026-10-03): "expected" carries
           no buffer, and the pre-buffer P90 is computed directly, never
           derived back by dividing.
  BUILT, NOT ADOPTED  simulated horizon P90 (2026-10-03, reverted on the
           user's decision): relief events/month ~ Poisson(climatology x
           P(relief)), sizes resampled from the LGU's real events, 50,000
           draws, fixed seed, 90th percentile of the horizon total.
           12-month P90 before buffer: Calasiao 46,030, Sta. Barbara
           20,919, Urdaneta 14,035 (vs 61,218 / 22,890 / 12,097 from the
           formula kept). Out-of-sample year replay (each year vs a
           simulation built without it): 4 of 5 years in every LGU, all
           three missing 2025 (Calasiao 57,778 vs 29,717; Sta. Barbara
           18,437 vs 17,752; Urdaneta 21,876 vs 3,331). Without the
           largest storm on record its P90 fell to 32,120 / 16,190 / 7,440.
  REJECTED minimum event size for the share fit - same result as weighting,
           with a magic number.
  REJECTED MAPE / R2 as headline metrics (2026-09-28) - see
           leave_one_typhoon_out_packs_cv; WAPE used instead.
  REJECTED affected-families relative-risk share model - tied v9.3.
  REJECTED shared-storm (cross-LGU) lognormal severity - its tail exploded
           for Sta. Barbara (median P90 ~180k packs); no coverage gain.
  NOT A MODEL  allocating by the storm's reported affected families: packs
           track affected families (~0.75-0.83 packs per family; Urdaneta
           1:1 in 40% of rows), so its ~40-67% lower share error mostly
           measures the CSWDOs' own rule. Out of the forecast metrics;
           possible separate allocation-support feature.
  SKIPPED  recency weighting - 14 storms can't tell a trend from luck, and
           the family-count change is partly a report-source change.
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
    """[(typhoon_key, start_date, key_date, year)] - every storm named in a
    real relief report (scripts/typhoon_calendar_from_reports.py)."""
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
    sheet, retired 2026-10-03 for its full report), not a needs report. Excluded from every history-based share
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
# 1.0 when allowed, but 0.75 scored the same: 0.0110 vs 0.0111 - on its
# earlier 7-report set.)
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
    (on its earlier 7-report set) and was about neutral elsewhere, but it does NOT clearly beat pooled
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


# Defense metrics (2026-10-03, agreed with the consultant): one metric per
# claim the model makes - see leave_one_typhoon_out_cv (skill score, ranking),
# leave_one_typhoon_out_packs_cv (WAPE), leave_one_typhoon_out_p90_coverage
# (pinball loss, shortfall/excess) and floor_protection.
PINBALL_TAU = 0.9
RANK_TOP_K = 5


def _avg_ranks(values):
    """Ranks 1..n, ties sharing their average rank (as Spearman needs)."""
    arr = np.asarray(values, dtype=float)
    order = arr.argsort(kind="mergesort")
    ranks = np.empty(len(arr))
    ranks[order] = np.arange(1, len(arr) + 1)
    for v in np.unique(arr):
        tie = arr == v
        if tie.sum() > 1:
            ranks[tie] = ranks[tie].mean()
    return ranks


def _spearman(x, y):
    """Spearman rank correlation, or None if either side is constant."""
    rx, ry = _avg_ranks(x), _avg_ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def _top_k_hit_rate(predicted, actual, k=RANK_TOP_K):
    """Of the k barangays ranked highest by `predicted`, the fraction that
    are really among the top k by `actual` - a barangay tied with the k-th
    largest actual value counts as a hit, so ties can't be unlucky."""
    bids = list(actual)
    top_pred = sorted(bids, key=lambda b: predicted.get(b, 0.0), reverse=True)[:k]
    kth = sorted((actual[b] for b in bids), reverse=True)[k - 1]
    return sum(1 for b in top_pred if actual[b] >= kth) / k


def _pinball(actual, quantile, tau=PINBALL_TAU):
    """Mean quantile (pinball) loss of a tau-quantile forecast: a shortfall
    costs tau per pack, an excess (1 - tau) per pack - so at tau = 0.9
    running short is penalised 9x more than overstocking, and an inflated
    P90 still pays for every unused pack."""
    a, q = np.asarray(actual, dtype=float), np.asarray(quantile, dtype=float)
    d = a - q
    return float(np.mean(np.where(d >= 0, tau * d, (tau - 1) * d)))


def _shortfall_excess(actual, quantile):
    """Readable companion to the pinball loss: how many cases ran short,
    by how much on average when they did, and how much was left over on
    average when they didn't (packs)."""
    a, q = np.asarray(actual, dtype=float), np.asarray(quantile, dtype=float)
    short = a > q
    return {
        "n_short": int(short.sum()),
        "n": int(len(a)),
        "avg_shortfall": float((a - q)[short].mean()) if short.any() else 0.0,
        "avg_excess": float((q - a)[~short].mean()) if (~short).any() else 0.0,
    }


def floor_protection(stage1, total_families_by_barangay):
    """What the 50% floor is FOR, counted on the final model: barangays
    whose pooled relief history would give them less than half their
    per-family share, and barangays the floor actually lifts in the current
    forecast (share before vs after apply_share_floor)."""
    tf = {bid: f for bid, f in total_families_by_barangay.items() if f}
    ftot = sum(tf.values())
    if not tf or ftot <= 0:
        return None
    history = stage1["history"] or {}
    hsum = sum(history.get(bid, 0.0) for bid in tf) or 1.0
    below_half = sum(1 for bid, f in tf.items()
                     if history.get(bid, 0.0) / hsum < SHARE_FLOOR * f / ftot)
    before = predict_shares(stage1["model"], tf, stage1["history"], stage1["alpha"], 0.0)
    after = predict_shares(stage1["model"], tf, stage1["history"], stage1["alpha"], SHARE_FLOOR)
    lifted = [bid for bid in tf if after[bid] > before[bid] + 1e-12]
    return {
        "n_barangays": len(tf),
        "n_history_below_half": below_half,
        "n_floor_lifted": len(lifted),
        "share_moved_by_floor": float(sum(after[b] - before[b] for b in lifted)),
    }


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
    rank = {"sp_model": [], "sp_pooled": [], "top_model": [], "top_pooled": []}
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

        # Ranking: does the model put the right barangays first? Only on
        # storms where at least RANK_TOP_K barangays got packs - in a 1-pack
        # storm there is no ranking to get right.
        packs = {r["barangay_id"]: r["food_packs_given"] for r in known}
        if sum(1 for v in packs.values() if v > 0) >= RANK_TOP_K:
            bids = list(packs)
            for name, pred in (("model", pred_share), ("pooled", pooled_share)):
                sp = _spearman([pred.get(b, 0.0) for b in bids], [packs[b] for b in bids])
                if sp is not None:
                    rank[f"sp_{name}"].append(sp)
                rank[f"top_{name}"].append(_top_k_hit_rate(pred, packs))

    if not err_model:
        return None

    # k of n: held-out storms where the model's share error beats pooled
    # history's (ties - e.g. both perfect - count as not beating).
    beats_k = sum(1 for _t, sm, sp, _n in per_event if sm < sp)
    # Bootstrap the size-weighted MAE difference over held-out storms.
    pe = np.array(per_event, dtype=float)
    rng = np.random.default_rng(0)
    diffs, skills = [], []
    for _ in range(2000):
        s = pe[rng.integers(0, len(pe), len(pe))]
        denom = (s[:, 0] * s[:, 3]).sum()
        diffs.append(((s[:, 0] * s[:, 1]).sum() - (s[:, 0] * s[:, 2]).sum()) / denom)
        pooled_err = (s[:, 0] * s[:, 2]).sum()
        if pooled_err > 0:
            skills.append(1 - (s[:, 0] * s[:, 1]).sum() / pooled_err)
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
    # Skill vs pooled history = 1 - model error / pooled-history error
    # (size-weighted): > 0 model better, < 0 worse, interval over 0 = tie.
    mae_w = float(np.average(err_model, weights=weights))
    pooled_w = float(np.average(err_pooled, weights=weights))
    skill = 1 - mae_w / pooled_w if pooled_w > 0 else None
    skill_lo, skill_hi = (np.percentile(skills, [2.5, 97.5]) if skills else (None, None))

    def _mean(xs):
        return float(np.mean(xs)) if xs else None
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
        "skill_vs_pooled": skill,
        "skill_vs_pooled_ci": (float(skill_lo), float(skill_hi)) if skills else None,
        # Ranking, averaged over held-out storms with >= RANK_TOP_K served.
        "spearman_model": _mean(rank["sp_model"]),
        "spearman_pooled": _mean(rank["sp_pooled"]),
        "top_k_model": _mean(rank["top_model"]),
        "top_k_pooled": _mean(rank["top_pooled"]),
        "top_k": RANK_TOP_K,
        "rank_n_storms": len(rank["top_model"]),
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
    divided by the calendar's typhoon count (the storms named in any LGU's
    relief reports - see module doc).

    Fixed 2026-10-03 (was: calendar typhoons COVERED by a relief record /
    36). The forecast multiplies this by severity, which is the mean size of
    a relief EVENT, and a combined report (e.g. Urdaneta's "Nika + Ofel +
    Pepito") is one event covering several storms - counting storms covered
    overstated historical totals by x1.36 (Urdaneta), x1.38 (Sta. Barbara)
    and x1.07 (Calasiao). A leave-one-year-out check put the new definition
    closer to the actual yearly total in 14 of 18 LGU-years; it fixes the
    bias in typical years and says nothing about 2025-type years, which no
    version predicts.

    Caveat: storms that brought no relief to ANY of the three LGUs are not
    in the calendar at all, so this is relief per reported storm, not per
    storm that passed near Pangasinan."""
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


def yearly_totals(events, calendar_rows):
    """{calendar year: real packs over all of this LGU's relief events that
    year} - the page compares the stockpile with the largest YEAR on record,
    not only the largest single storm, since the stockpile formula (expected
    storms x per-storm P90) is not a true yearly percentile. A combined
    report counts in the year of its first named storm."""
    year_of_key = {r[0]: r[3] for r in calendar_rows}
    out = {}
    for ev in events.values():
        total = _event_total_and_known(ev["records"])[0]
        if total <= 0:
            continue
        year = next((year_of_key[k] for k in ev["typhoon_keys"] if k in year_of_key), None)
        if year is None:
            d = _as_date(ev["report_date"])
            year = d.year if d else None
        if year is not None:
            out[year] = out.get(year, 0) + total
    return out


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
    baggage. WAPE (sum |miss| / sum real packs, 2026-10-03) is the
    percentage figure in MAPE's place."""
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
        # WAPE = total |miss| / total real packs - the "% error" MAPE was
        # meant to give, without blowing up on near-zero barangays.
        "wape": float(np.abs(err).sum() / a.sum()) if a.sum() > 0 else None,
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

    Two levels, both leave-one-typhoon-out, scored on the raw P90 without
    the (1 + BUFFER) margin - the buffer is a policy choice and is not
    counted as coverage:
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
    real LGU total; none loaded since 2026-10-03); the barangay-level figures
    skip it, since it has no family counts to split by. So the two levels
    can be over different storm counts.
    None if there isn't enough data to run a single fold."""
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    lgu_hits = lgu_n = brgy_hits = brgy_n = nz_hits = nz_n = 0
    lgu_pairs, nz_pairs = [], []  # (real packs, P90 packs) for pinball/shortfall
    for held_out in scoreable:
        sev = _loto_severity_excluding(events, held_out)
        if sev is None:
            continue
        total, known = _event_total_and_known(events[held_out]["records"])

        lgu_hits += int(total <= sev["high"])  # every event with packs, supply-only included
        lgu_n += 1
        lgu_pairs.append((total, sev["high"]))

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
                nz_pairs.append((r["food_packs_given"], p90_packs))

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
        # Pinball loss at tau 0.9 (packs) + readable shortfall/excess, at
        # the municipality level and over barangays that received packs.
        "pinball_lgu": _pinball(*zip(*lgu_pairs)),
        "pinball_barangay_nonzero": _pinball(*zip(*nz_pairs)) if nz_pairs else None,
        "shortfall_lgu": _shortfall_excess(*zip(*lgu_pairs)),
        "shortfall_barangay_nonzero": _shortfall_excess(*zip(*nz_pairs)) if nz_pairs else None,
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
            "then scripts/load_relief_events.py first."
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
            # Real packs per calendar year - the "largest year on record"
            # comparison on the page.
            "yearly_totals": yearly_totals(events, calendar_rows),
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
        if loto_cv[lgu] is not None:
            loto_cv[lgu]["floor"] = floor_protection(stage1, latest_tf)
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
