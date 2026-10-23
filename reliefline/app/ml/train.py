# Trains the food pack forecast model from past typhoon relief records.

import os
import statistics
from datetime import date

from app.utils.timezone import ph_now, ph_today

import numpy as np
import joblib

MODEL_VERSION = "v9.3-two-stage-lgu"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")

# 15% safety buffer added on top of the recommended stockpile.
BUFFER = 0.15

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# Turns text like '1,234' into a number (returns nothing if it isn't a number).
def _to_number(value):
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


# Food packs actually given in an allocation:
# the approved amount, or the requested amount if nothing was approved yet.
def _realized_quantity(alloc):
    if alloc.allocated_quantity:
        return alloc.allocated_quantity
    return alloc.predicted_quantity or 0


# A barangay's typical food packs per disaster in the past (the middle value).
# Shown as 'Historical Allocation' on the barangay list.
def historical_allocation_for(barangay_id, before_date=None):
    from app.models.allocation import AllocationRecord

    q = AllocationRecord.query.filter(
        AllocationRecord.barangay_id == barangay_id,
        AllocationRecord.status.in_(("approved", "released")),
    )
    if before_date is not None:
        q = q.filter(AllocationRecord.allocation_date < before_date)
    return _median_event_allocation(q.all())


# The middle (median) number of food packs per disaster, from a list of allocations.
def _median_event_allocation(records):
    if not records:
        return 0

    per_event = {}
    for rec in records:
        key = rec.event_id if rec.event_id is not None else ("solo", rec.allocation_id)
        per_event[key] = per_event.get(key, 0) + _realized_quantity(rec)

    return float(statistics.median(per_event.values()))


# Loads the real past typhoon relief records from the database, grouped by municipality.
# This is the data the forecast model learns from.
def load_relief_data():
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


# Turns text into a date.
def _as_date(value):
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


# Loads the PAGASA list of typhoons that affected Pangasinan (2021-2026) from the database.
def load_typhoon_calendar():
    from sqlalchemy import text
    from app.extensions import db

    return db.session.execute(text(
        "SELECT typhoon_key, start_date, key_date, year FROM typhoon_calendar")).fetchall()


# For one typhoon: the total food packs given,
# and the barangay records that have actual numbers.
def _event_total_and_known(records):
    known = [r for r in records if r["food_packs_given"] is not None]
    total = sum(r["food_packs_given"] for r in known)
    return total, known


# Prepares the data used to learn each barangay's share of relief
# (number of families vs share of packs received).
def _share_training_rows(events):
    rows = []
    for ev in events.values():
        total, known = _event_total_and_known(ev["records"])
        if total <= 0 or len(known) < 2:
            continue
        for r in known:
            if r["total_families_snapshot"] is not None:
                rows.append((r["total_families_snapshot"], r["food_packs_given"] / total, total))
    return rows


# Learns how a barangay's share of relief relates to its number of families
# (more families usually means a bigger share).
def fit_share_model(rows):
    if len(rows) < 3:
        return None
    x = np.array([r[0] for r in rows], dtype=float)
    y = np.array([r[1] for r in rows], dtype=float)
    w = np.sqrt(np.array([r[2] for r in rows], dtype=float))
    slope, intercept = np.polyfit(x, y, 1, w=w)
    return {"slope": float(slope), "intercept": float(intercept), "n_rows": len(rows),
            "weighting": "event_total"}


# Estimates each barangay's share of the municipality's food packs,
# mixing the family-count estimate with the barangay's past relief history.
def predict_shares(model, total_families_by_barangay, history=None, alpha=0.0, floor=0.0):
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


# Makes sure no barangay gets less than a minimum fair share
# (at least half of what its number of families alone would give it).
def apply_share_floor(shares, total_families_by_barangay, floor):
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


# True if a typhoon record has no family counts (only supply numbers).
def _is_supply_only(known):
    return not any(r["total_families_snapshot"] is not None for r in known)


# Each barangay's average share of relief across all past typhoons.
def pooled_history_shares(events):
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


ALPHA_GRID = (0.0, 0.25, 0.5, 0.75)
# Minimum fair share: a barangay gets at least half of what its family count alone would give it.
SHARE_FLOOR = 0.5

_STAGE1_CACHE = {}


# Lists the typhoons that have enough data to test the model on.
def _scoreable_with_families(events):
    out = []
    for eid, ev in events.items():
        total, known = _event_total_and_known(ev["records"])
        if total > 0 and len(known) >= 2 and all(r["total_families_snapshot"] is not None for r in known):
            out.append(eid)
    return out


# Measures how far off the share estimates are,
# so training can pick the best mix of history vs family count.
def _weighted_share_error(events, alpha):
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


# Trains Stage 1 of the model: how a municipality's food packs are split among its barangays.
def fit_stage1(events):
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


# Uses the trained Stage 1 to estimate each barangay's share.
def stage1_shares(stage1, total_families_by_barangay):
    return predict_shares(stage1["model"], total_families_by_barangay,
                          stage1["history"], stage1["alpha"], SHARE_FLOOR)


PINBALL_TAU = 0.9
RANK_TOP_K = 5


# Ranks numbers from smallest to largest (equal numbers share the same rank).
def _avg_ranks(values):
    arr = np.asarray(values, dtype=float)
    order = arr.argsort(kind="mergesort")
    ranks = np.empty(len(arr))
    ranks[order] = np.arange(1, len(arr) + 1)
    for v in np.unique(arr):
        tie = arr == v
        if tie.sum() > 1:
            ranks[tie] = ranks[tie].mean()
    return ranks


# Measures how well the predicted order of barangays (most to least need)
# matches the real order. 1.0 = perfect match.
def _spearman(x, y):
    rx, ry = _avg_ranks(x), _avg_ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


# How many of the barangays the model ranked in the top 5 were really in the top 5.
def _top_k_hit_rate(predicted, actual, k=RANK_TOP_K):
    bids = list(actual)
    top_pred = sorted(bids, key=lambda b: predicted.get(b, 0.0), reverse=True)[:k]
    kth = sorted((actual[b] for b in bids), reverse=True)[k - 1]
    return sum(1 for b in top_pred if actual[b] >= kth) / k


# Scores the recommended stockpile: running short is penalized more than having extra,
# so a stockpile can't look good just by being huge.
def _pinball(actual, quantile, tau=PINBALL_TAU):
    a, q = np.asarray(actual, dtype=float), np.asarray(quantile, dtype=float)
    d = a - q
    return float(np.mean(np.where(d >= 0, tau * d, (tau - 1) * d)))


# Counts how often, and by how much, the stockpile would have been short or had extra.
def _shortfall_excess(actual, quantile):
    a, q = np.asarray(actual, dtype=float), np.asarray(quantile, dtype=float)
    short = a > q
    return {
        "n_short": int(short.sum()),
        "n": int(len(a)),
        "avg_shortfall": float((a - q)[short].mean()) if short.any() else 0.0,
        "avg_excess": float((q - a)[~short].mean()) if (~short).any() else 0.0,
    }


# Reports which barangays the minimum fair share protects, and by how much.
def floor_protection(stage1, total_families_by_barangay):
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


# Tests the barangay-share model fairly: hide one typhoon, train on the rest, predict the hidden one, compare.
# This is repeated for every typhoon to get the accuracy shown on the Model Accuracy panel.
def leave_one_typhoon_out_cv(events):
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    err_model, err_equal, err_avg, err_pooled, weights = [], [], [], [], []
    per_event = []
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
            continue
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

    beats_k = sum(1 for _t, sm, sp, _n in per_event if sm < sp)
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
    mae_w = float(np.average(err_model, weights=weights))
    pooled_w = float(np.average(err_pooled, weights=weights))
    skill = 1 - mae_w / pooled_w if pooled_w > 0 else None
    skill_lo, skill_hi = (np.percentile(skills, [2.5, 97.5]) if skills else (None, None))

    # Average of a list of numbers.
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
        "spearman_model": _mean(rank["sp_model"]),
        "spearman_pooled": _mean(rank["sp_pooled"]),
        "top_k_model": _mean(rank["top_model"]),
        "top_k_pooled": _mean(rank["top_pooled"]),
        "top_k": RANK_TOP_K,
        "rank_n_storms": len(rank["top_model"]),
        "n_folds": len(per_event),
        "n_rows": len(err_model),
    }


# How many typhoons to expect in each month of the year,
# based on the PAGASA list of typhoons from 2021-2026.
def climatology_by_month(calendar_rows, today):
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


# The chance that a typhoon leads to a relief operation
# (relief operations divided by the number of typhoons on the PAGASA list).
def p_relief(events, all_typhoon_keys):
    universe = set(all_typhoon_keys)
    if not universe:
        return 0.0
    n_events = sum(1 for ev in events.values()
                   if set(ev["typhoon_keys"]) & universe and _event_total_and_known(ev["records"])[0] > 0)
    return n_events / len(universe)


# How many food packs one typhoon usually needs: low, expected (average) and high (P90).
def severity_scenarios(events):
    totals = [t for ev in events.values() if (t := _event_total_and_known(ev["records"])[0]) > 0]
    if not totals:
        return {"low": 0.0, "expected": 0.0, "high": 0.0, "n": 0}
    arr = np.array(totals, dtype=float)
    return {
        "low": float(np.percentile(arr, 25)),
        "expected": float(arr.mean()),
        "high": float(np.percentile(arr, 90)),
        "max": float(arr.max()),
        "n": len(totals),
    }


# Total food packs given out per year.
def yearly_totals(events, calendar_rows):
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


# Typhoon size figures computed without one typhoon (used for fair testing).
def _loto_severity_excluding(events, exclude_eid):
    totals = [t for eid, ev in events.items() if eid != exclude_eid
              and (t := _event_total_and_known(ev["records"])[0]) > 0]
    if not totals:
        return None
    arr = np.array(totals, dtype=float)
    return {"expected": float(arr.mean()), "high": float(np.percentile(arr, 90))}


# Builds the data points for the 'actual vs predicted' chart.
def _backtest_points(events, calendar_by_key):
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


# Tests the food pack forecast: hide one typhoon, predict it, compare with what really happened.
# Repeated for every typhoon.
def leave_one_typhoon_out_packs_cv(events):
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
        "wape": float(np.abs(err).sum() / a.sum()) if a.sum() > 0 else None,
        "n": len(a),
    }


# Tests how often the recommended stockpile would have been enough for a hidden typhoon
# (for the municipality and for each barangay).
def leave_one_typhoon_out_p90_coverage(events):
    scoreable = [eid for eid, ev in events.items() if _event_total_and_known(ev["records"])[0] > 0
                 and len(_event_total_and_known(ev["records"])[1]) >= 2]
    if len(scoreable) < 2:
        return None

    lgu_hits = lgu_n = brgy_hits = brgy_n = nz_hits = nz_n = 0
    lgu_pairs, nz_pairs = [], []
    for held_out in scoreable:
        sev = _loto_severity_excluding(events, held_out)
        if sev is None:
            continue
        total, known = _event_total_and_known(events[held_out]["records"])

        lgu_hits += int(total <= sev["high"])
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
        "pinball_lgu": _pinball(*zip(*lgu_pairs)),
        "pinball_barangay_nonzero": _pinball(*zip(*nz_pairs)) if nz_pairs else None,
        "shortfall_lgu": _shortfall_excess(*zip(*lgu_pairs)),
        "shortfall_barangay_nonzero": _shortfall_excess(*zip(*nz_pairs)) if nz_pairs else None,
    }


# Trains the whole forecast model from the database and saves it to the model file.
# Also saves its accuracy scores. Run it with scripts/train_model.py when new relief data comes in.
def train_and_persist():
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    _STAGE1_CACHE.clear()
    by_lgu = load_relief_data()
    if not by_lgu:
        raise RuntimeError(
            "No relief_events found - load database/reliefline_db.sql, which carries the real relief data."
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
            "yearly_totals": yearly_totals(events, calendar_rows),
            "barangays": {bid: {"latest_total_families": tf} for bid, tf in latest_tf.items()},
            "event_ids": sorted(events),
            "n_events_with_packs": sum(1 for ev in events.values()
                                       if _event_total_and_known(ev["records"])[0] > 0),
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
                {"month": p["date"].strftime("%Y-%m"),
                 "actual": p["actual"], "expected": p["expected"], "p90": p["p90"]}
                for p in _backtest_points(events, calendar_by_key)
            ],
        }

    if not lgu_artifact:
        raise RuntimeError("Not enough real relief data to fit a share model for any LGU.")

    data_through = ph_today().isoformat()
    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    # Save the trained model to the file the app reads when making forecasts.
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
        db.session.add(ModelMetrics(
            model_version=MODEL_VERSION,
            mae=round(max(cv["mae_model"] for cv in scored.values()), 4),
            mae_baseline_equal_split=round(max(cv["mae_equal_split"] for cv in scored.values()), 4),
            mae_baseline_avg_share=round(max(cv["mae_avg_share"] for cv in scored.values()), 4),
            mae_packs=round(max(cv["mae_packs"] for cv in packs_scored.values()), 4) if packs_scored else None,
            rmse=round(max(cv["rmse_packs"] for cv in packs_scored.values()), 4) if packs_scored else None,
            p90_coverage=round(min(cv["barangay_coverage_nonzero"] for cv in p90_scored.values()
                                   if cv.get("barangay_coverage_nonzero") is not None), 4) if p90_scored else None,
            training_samples=sum(len(ev["records"]) for events in by_lgu.values() for ev in events.values()),
        ))
        db.session.commit()

    return {"lgus": list(lgu_artifact), "loto_cv": loto_cv, "loto_packs_cv": loto_packs_cv,
            "loto_p90": loto_p90, "data_through": data_through}
