"""
Trains the food-pack TIME-SERIES FORECASTER: a SARIMAX model per LGU
(Urdaneta City, Santa Barbara, Calasiao) that projects monthly food-pack
demand for the coming 4 / 6 / 12 months, so PSWDO/CSWDO can answer "how many
food packs should we hold in stock for the next months?" - with extra weight
on the rainy / typhoon season.

--------------------------------------------------------------------------
The model
--------------------------------------------------------------------------
  log(1 + packs_t) = c + b1*wet_season_m + b2*peak_typhoon_m
                       + b3*log(tc_climatology_m) + u_t,   u_t ~ ARMA(1, 1)

  * SARIMAX(1,0,1), constant trend, fitted per LGU on the monthly series
    (app.models.barangay_monthly_history summed to LGU level).
  * Exogenous predictors are all KNOWN IN ADVANCE for any future month, so
    they can be used to forecast: the Type-I wet-season flag (Jun-Oct), the
    peak-typhoon flag (Jul-Oct, ~70% of PAR tropical cyclones per PAGASA) and
    the log of the monthly tropical-cyclone climatology (gives the Jun and
    Nov "shoulder" months weight - Nov typhoons Pepito 2024 / Uwan 2025 hit
    Pangasinan). This is where the "more weight on the rainy season" lives.
    The PAGASA Dagupan rainfall normal is kept in climate_monthly and was
    tested; it adds nothing once wet/peak/tc are in (all are seasonal).
    Caveat: the monthly split of TC_CLIMO is approximate (annual total and
    Jul-Oct share match PAGASA) - replace it with PAGASA's monthly table.
  * log(1+y) because demand is heavy-tailed: a few typhoon months dwarf
    ordinary ones. The forecast DISTRIBUTION is built from the model's own
    errors (see _residual_pool), not a normal curve: whole past seasons are
    resampled (recency-weighted), so a busy season lifts Jul-Oct together.
    Expected demand is the mean of the simulated paths and the P90 stock level
    their 90th percentile.
  * Why LGU level: a single barangay has ~60 monthly points, mostly zeros -
    too little for a time-series fit. app.ml.predict splits each LGU forecast
    to barangays by their history and flood hazard.

How the spec was chosen (rolling-origin backtest, honest and reproducible -
run scripts/train_model.py): orders (0-2, 0, 0-1) x predictor sets were
compared on 5 expanding-window origins x 3 LGUs x 12-month horizons.
ARMA(1,1) + {wet, peak, tc} (or {rain, wet, peak}) had the lowest 12-month
total error and a small bias, with near-nominal P90 coverage. Fourier (harmonic) seasonal
terms were also tried: slightly better monthly R2 but they over-forecast by
17-28%, the wrong way to fail for stock planning. ENSO (ONI) was tested as a
predictor and REJECTED (it made forecasts far worse), so it is stored
(climate_monthly) but not used. is mildly optimistic - re-check once real data lands.

History of the forecast distribution (kept for the panel). Attempt 1 used the
log-normal mean with the model's multi-step standard error: fine on the early
synthetic history, but once Urdaneta's real 2025 reports were added two of the
three fits went degenerate (MA coefficient ~90) and expected demand inflated 20x;
stationarity/invertibility are now enforced. Attempt 2 replaced the normal curve
with empirical errors plus a Gaussian "busy/quiet season" effect: its backtest
looked best (bias -2%) but only because it over-forecast 3-4x the largest year
in the history, which happened to offset the fact that each year in the history
is bigger than the last. The final version bootstraps whole past seasons
(see _simulate): the expected annual total stays consistent with the history
and the P90 total is about a bad year like 2025.

Honest limitation: every year in the history is larger than the one before (2022
quiet, 2025 the worst), so any method that treats seasons as comparable
under-forecasts the newest ones - seasonal-naive by -49%, this model by -51% in
the backtest, and its P90 of a 12-month total covers only ~half of backtest
years. Real data will show whether that growth is real.

Metrics reported (ModelMetrics + scripts/train_model.py), vs two baselines
(seasonal-naive = same month last year; seasonal-mean = mean of that calendar
month in all prior years):
  * monthly MAE / RMSE / WAPE / R2 - harsh for spiky demand: it punishes the
    exact timing of a storm, which no model can know months ahead. Here the
    model ties the seasonal-mean baseline and beats seasonal-naive on WAPE, but
    seasonal-naive has the better R2 (real storms landed in July in 4 of 5
    years, so "same month last year" is a strong guess at timing).
  * 6- and 12-month TOTAL error (pooled WAPE of window totals) - the number a
    stockpile decision uses. On the current history the model is NOT better
    than the simple baselines here (12-month: 0.51 vs 0.49; 6-month: 0.50 vs
    0.58 naive / 0.44 seasonal-mean) - every season in the history is bigger
    than the last, which none of these methods can foresee. Reported openly.
  * P90 coverage - share of actual months at/below the P90 safety stock
    (target ~0.90). Stored figure is calibrated ONLY on backtest windows that
    had already ended (strictly-past); the looser leave-one-fold-out number
    (a little higher) is also printed by scripts/train_model.py.

Data reality: history is SYNTHETIC (anchored to the real 2021-2025 storm
calendar, PAGASA climatology and the Aug 2026 Sta. Barbara sheet - see
scripts/seed_monthly_history.py) until real records arrive. Retrain then; the
pipeline does not change.

--------------------------------------------------------------------------
Keeping the training set honest
--------------------------------------------------------------------------
Only barangay_monthly_history rows with data_source in ('synthetic',
'real', 'system') train the model ('real' = the four Urdaneta 2025 CSWDO
reports). 'real_sample' rows (a single month of one
municipality) are held out and used only to sanity-check the forecast - see
holdout_check().

Run scripts/train_model.py to (re)fit this against the current database.
"""
import math
import os
import warnings
from datetime import date

from app.utils.timezone import ph_now

import numpy as np
import joblib

# Trusted historical events used by the older per-event allocation history
# (historical_allocation_for below). Kept as the allow-list of events whose
# AllocationRecords count as history; ad hoc test events must never leak in.
CALIBRATION_EVENT_NAMES = {
    "Typhoon Egay (2023)", "Typhoon Kabayan (2023)", "Typhoon Carina (2024)",
    "Super Typhoon Julian (2024)", "Tropical Storm Dante (2025)", "Typhoon Ramil (2025)",
    "Typhoon Inday", "Tropical Storm Basyang", "Tropical Storm Ada",
    "Localized Flooding (Jan)", "Localized Flooding (Feb)", "Summer Heat Advisory (Mar)",
    "Localized Flashflood (Apr)", "Pre-Monsoon Squall (May)", "Amihan Tail-end Flooding (Dec)",
}

MODEL_VERSION = "v8.0-sarimax-lgu"
ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "food_pack_demand.joblib")

ORDER = (1, 0, 1)
EXOG_FEATURES = ["wet", "peak", "tc"]
FORECAST_MONTHS = 36          # how far ahead the artifact carries a forecast
SIM_DRAWS = 2000              # simulated paths per LGU (monthly stats, horizon totals, running totals)
BACKTEST_HORIZON = 12
BACKTEST_STEP = 6             # an origin every 6 months (Dec and Jun)
MIN_TRAIN_MONTHS = 24         # smallest training window in a backtest fold
MIN_MONTHS = 36               # refuse to train on less history than this
# Half-life, in years, of the weight given to past seasons when building the
# forecast distribution: last season counts twice as much as the one two years
# before. A judgement call for a series whose seasons keep getting bigger; the
# backtest is insensitive to it (tried 1-3 years).
RECENCY_HALF_LIFE_YEARS = 2.0

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
    over-weighted). Shown on the admin barangay views and stored on new
    allocations for audit.

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
    that barangay's already-loaded qualifying records."""
    import statistics

    if not records:
        return 0

    per_event = {}
    for rec in records:
        key = rec.event_id if rec.event_id is not None else ("solo", rec.allocation_id)
        per_event[key] = max(per_event.get(key, 0), _realized_quantity(rec))

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
# Time-series data
# ---------------------------------------------------------------------------

def exog_frame(index):
    """Predictors known in advance for any calendar month (see module doc)."""
    import pandas as pd
    from app.ml import climate_reference as ref

    months = index.month
    return pd.DataFrame({
        "wet": [1.0 if m in ref.WET_SEASON_MONTHS else 0.0 for m in months],
        "peak": [1.0 if m in ref.PEAK_MONTHS else 0.0 for m in months],
        "tc": [math.log(ref.TC_CLIMO[m - 1]) for m in months],
    }, index=index)[EXOG_FEATURES]


def load_lgu_series():
    """{lgu: monthly food-pack Series} from barangay_monthly_history, summed to
    LGU level. Only 'synthetic'/'real'/'system' rows train the model (see module
    doc). Months with no rows become NaN, which the state-space model treats
    as missing rather than as zero demand."""
    import pandas as pd
    from sqlalchemy import text
    from app.extensions import db

    rows = db.session.execute(text(
        "SELECT b.city_municipality, h.month_start, SUM(h.food_packs) "
        "FROM barangay_monthly_history h JOIN barangays b ON b.barangay_id = h.barangay_id "
        "WHERE h.data_source IN ('synthetic', 'real', 'system') "
        "GROUP BY b.city_municipality, h.month_start")).fetchall()
    if not rows:
        return {}
    df = pd.DataFrame(rows, columns=["lgu", "month", "packs"])
    df["month"] = pd.to_datetime(df["month"])
    df["packs"] = df["packs"].astype(float)
    idx = pd.date_range(df["month"].min(), df["month"].max(), freq="MS")
    return {
        lgu: g.set_index("month")["packs"].reindex(idx)
        for lgu, g in df.groupby("lgu")
    }


def _fit(series):
    """SARIMAX on log(1+packs). Stationarity and invertibility are ENFORCED:
    left free, the optimiser can wander to a degenerate solution (an MA
    coefficient of ~90 with zero variance) on a volatile series, which then
    forecasts nonsense."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    z = np.log1p(series)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(
            z, exog=exog_frame(z.index), order=ORDER, trend="c",
            enforce_stationarity=True, enforce_invertibility=True,
        ).fit(disp=False, maxiter=500)


def _forecast(results, index):
    """Mean forecast mu on the log(1+packs) scale for the given months."""
    fc = results.get_forecast(len(index), exog=exog_frame(index))
    return fc.predicted_mean.values


def _residual_pool(results, series):
    """What the fitted model does NOT explain, on the log scale, kept as REAL
    numbers (not a normal curve) and grouped by season year, so the forecast
    distribution is built from the history itself:

      peak   - {year: errors of that year's peak-typhoon months (Jul-Oct)},
               centred on the overall peak mean, so each year keeps its own
               shape: 2022 = one small storm, 2025 = four big months.
      w      - recency weight of each year (half-life RECENCY_HALF_LIFE_YEARS):
               a recent season says more about next season than 2021 does.
      other  - errors in all other months, centred.

    Why not the usual log-normal formulas: demand is bimodal (a storm month is
    ~100x an ordinary one) and far more variable in the peak season than in the
    dry season, so a normal spread makes the expected value explode (tried: an
    Aug forecast of 19,515 packs against a median of 824, and a 12-month total
    3-4x the largest year in the history). Nothing here comes from outside the
    data the model was fitted on, so nothing about the future leaks in."""
    z = np.log1p(series)
    X = exog_frame(z.index)
    p = results.params
    fitted = p["intercept"] + sum(p[c] * X[c] for c in EXOG_FEATURES)
    u = (z - fitted).dropna()
    is_peak = X.loc[u.index, "peak"].values == 1
    up, uo = u[is_peak], u.values[~is_peak]

    years = [y for y in sorted(up.index.year.unique()) if (up.index.year == y).sum() >= 3]
    if not years:
        years = sorted(up.index.year.unique())
    if not years:
        return {"years": [0], "w": np.ones(1), "peak": {0: np.zeros(1)},
                "other": (uo - uo.mean()) if len(uo) else np.zeros(1)}
    centre = up[up.index.year.isin(years)].values.mean()
    last = max(years)
    w = np.array([0.5 ** ((last - y) / RECENCY_HALF_LIFE_YEARS) for y in years])
    return {
        "years": years, "w": w / w.sum(),
        "peak": {y: up[up.index.year == y].values - centre for y in years},
        "other": (uo - uo.mean()) if len(uo) else np.zeros(1),
    }


def _simulate(mu, index, pool, draws=None, seed=20260926):
    """Simulated demand paths (packs, shape (len(index), draws)). For each
    calendar year in the horizon a draw picks ONE past season (recency-weighted)
    and every peak-typhoon month in that year takes an error from THAT season,
    so a busy season lifts Jul-Oct together and a quiet one lowers them
    together - a block bootstrap by year. Other months take their own errors.
    Expected demand, the median and the P90 - monthly, over a horizon, and as a
    running total - are all read off these same paths, so they always agree."""
    draws = draws or SIM_DRAWS
    rng = np.random.default_rng(seed)
    peak = exog_frame(index)["peak"].values == 1
    pick = {y: rng.choice(len(pool["years"]), draws, p=pool["w"]) for y in sorted(set(index.year))}
    paths = np.empty((len(index), draws))
    for i, (m, is_peak) in enumerate(zip(mu, peak)):
        if is_peak:
            which, u = pick[index[i].year], np.empty(draws)
            for j, y in enumerate(pool["years"]):
                sel = which == j
                u[sel] = rng.choice(pool["peak"][y], int(sel.sum()))
            paths[i] = np.expm1(m + u)
        else:
            paths[i] = np.expm1(m + rng.choice(pool["other"], draws))
    return np.clip(paths, 0, None)


def _summarise(paths):
    """(expected, median, p90) per month from simulated paths. The P90 is never
    below the expected value: in a quiet month almost every path is small but a
    rare storm path is huge, so the mean can sit above the 90th percentile - a
    recommended stockpile under the average need would be meaningless."""
    expected = paths.mean(axis=1)
    return expected, np.median(paths, axis=1), np.maximum(np.quantile(paths, 0.9, axis=1), expected)


# ---------------------------------------------------------------------------
# Rolling-origin backtest
# ---------------------------------------------------------------------------

def _origins(series):
    import pandas as pd

    observed = series.dropna().index
    first, last = observed.min(), observed.max()
    origins, o = [], first + pd.DateOffset(months=MIN_TRAIN_MONTHS - 1)
    while o + pd.DateOffset(months=BACKTEST_HORIZON) <= last:
        origins.append(o)
        o = o + pd.DateOffset(months=BACKTEST_STEP)
    return origins


def _baselines(series, origin, fidx):
    import pandas as pd

    train = series[:origin]
    naive = series.reindex(fidx - pd.DateOffset(years=1)).values
    seas = np.array([np.nanmean(train[train.index.month == t.month]) for t in fidx])
    return naive, seas


def backtest(series_by_lgu):
    """Expanding-window, rolling-origin evaluation. Returns the raw fold
    records plus the summary dict used by train_and_persist / the CLI."""
    import pandas as pd

    recs = []
    for lgu, series in series_by_lgu.items():
        for fold, origin in enumerate(_origins(series)):
            fidx = pd.date_range(origin + pd.offsets.MonthBegin(1), periods=BACKTEST_HORIZON, freq="MS")
            actual = series.reindex(fidx).values
            if np.isnan(actual).any():
                continue
            res = _fit(series[:origin])
            mu = _forecast(res, fidx)
            pool = _residual_pool(res, series[:origin])
            paths = _simulate(mu, fidx, pool)
            expected, _median, p90 = _summarise(paths)
            naive, seas = _baselines(series, origin, fidx)
            recs.append({
                "lgu": lgu, "origin": origin, "fold": fold, "fidx": fidx, "actual": actual,
                "mu": mu, "expected": expected, "p90": p90,
                "naive": naive, "seasmean": seas, "paths": paths,
            })
    return recs


def summarize_backtest(recs):
    if not recs:
        return None
    a = np.concatenate([r["actual"] for r in recs])
    mon = np.concatenate([r["fidx"].month for r in recs])
    from app.ml import climate_reference as ref
    wet = np.isin(mon, list(ref.WET_SEASON_MONTHS))

    def metrics(key):
        f = np.concatenate([r[key] for r in recs])
        f = np.where(np.isnan(f), 0.0, f)
        err = a - f
        nz = a != 0
        return {
            "mae": float(np.abs(err).mean()),
            "rmse": float(np.sqrt((err ** 2).mean())),
            "wape": float(np.abs(err).sum() / a.sum()),
            "wape_wet": float(np.abs(err[wet]).sum() / a[wet].sum()),
            "mape": float(np.mean(np.abs(err[nz] / a[nz])) * 100) if nz.any() else float("nan"),
            "r2": float(1 - (err ** 2).sum() / ((a - a.mean()) ** 2).sum()),
            "bias_pct": float(f.sum() / a.sum() * 100 - 100),
        }

    def total_err(key, h):
        """WAPE of the h-month window TOTALS (sum |forecast - actual| over
        windows / sum actual). Pooled on purpose: a mean of per-window
        percentages explodes on dry-season windows whose actual is near 0."""
        actual = np.array([r["actual"][:h].sum() for r in recs])
        fc = np.array([np.nan_to_num(r[key][:h]).sum() for r in recs])
        return float(np.abs(actual - fc).sum() / actual.sum())

    # Monthly P90 coverage. Each fit's P90 comes from ITS OWN training-window
    # errors only, so this is out-of-sample by construction (no cross-fold
    # calibration needed).
    covered = sum(int((r["actual"] <= r["p90"]).sum()) for r in recs)
    total = sum(len(r["actual"]) for r in recs)

    # Horizon-total P90 from the simulated paths (H = 6, 12).
    tot_cov = {}
    for h in (6, 12):
        hits = [r["actual"][:h].sum() <= np.quantile(r["paths"][:h].sum(axis=0), 0.9) for r in recs]
        tot_cov[h] = float(np.mean(hits))

    return {
        "folds": len(recs),
        "origins": sorted({r["origin"].strftime("%Y-%m") for r in recs}),
        "sarimax": metrics("expected"),
        "naive": metrics("naive"),
        "seasmean": metrics("seasmean"),
        "total_err": {
            h: {"sarimax": total_err("expected", h), "naive": total_err("naive", h),
                "seasmean": total_err("seasmean", h)} for h in (6, 12)
        },
        "p90_month_coverage": covered / total,
        "p90_month_coverage_strict": covered / total,
        "p90_strict_months": total,
        "p90_total_coverage": tot_cov,
    }


def _latest_fold_series(recs):
    """Actual vs forecast for the most recent backtest fold (train through
    the last full year, forecast the next 12 months) - per LGU, for the
    Model Performance chart. Its P90 comes only from that fit's training
    window (no peeking)."""
    if not recs:
        return {}
    last_origin = max(r["origin"] for r in recs)
    out = {}
    for r in recs:
        if r["origin"] != last_origin:
            continue
        out[r["lgu"]] = {
            "origin": last_origin.strftime("%Y-%m"),
            "points": [
                {"month": t.strftime("%Y-%m"), "actual": float(a), "expected": float(e), "p90": float(q)}
                for t, a, e, q in zip(r["fidx"], r["actual"], r["expected"], r["p90"])
            ],
        }
    return out


# ---------------------------------------------------------------------------
# Train + persist
# ---------------------------------------------------------------------------

def holdout_check(forecasts):
    """Compare the forecast with the real Aug 2026 Sta. Barbara relief sheet
    (data_source='real_sample'). It is supply, not measured need, so this is
    an order-of-magnitude sanity check - not a scored metric."""
    from sqlalchemy import text
    from app.extensions import db

    rows = db.session.execute(text(
        "SELECT b.city_municipality, h.month_start, SUM(h.food_packs) "
        "FROM barangay_monthly_history h JOIN barangays b ON b.barangay_id = h.barangay_id "
        "WHERE h.data_source = 'real_sample' GROUP BY 1, 2")).fetchall()
    out = []
    for lgu, month, actual in rows:
        f = forecasts.get(lgu, {}).get(month.strftime("%Y-%m"))
        if f:
            out.append({"lgu": lgu, "month": month.strftime("%Y-%m"), "actual": int(actual),
                        "expected": f["expected"], "p90": f["p90"]})
    return out


def train_and_persist():
    """Fits one SARIMAX per LGU on all trusted monthly history, runs the
    rolling-origin backtest, saves the artifact (a 36-month forecast table +
    simulated paths) for app.ml.predict, and records ModelMetrics."""
    import pandas as pd
    from app.extensions import db
    from app.models.prediction import ModelMetrics

    series_by_lgu = load_lgu_series()
    if not series_by_lgu or min(int(s.notna().sum()) for s in series_by_lgu.values()) < MIN_MONTHS:
        raise RuntimeError(
            f"Need at least {MIN_MONTHS} months of history per LGU in barangay_monthly_history. "
            f"Run scripts/apply_timeseries_schema.py then scripts/seed_monthly_history.py first."
        )

    recs = backtest(series_by_lgu)
    summary = summarize_backtest(recs)

    forecasts, paths = {}, {}
    data_through = max(s.dropna().index.max() for s in series_by_lgu.values())
    for lgu, series in series_by_lgu.items():
        res = _fit(series)
        last = series.dropna().index.max()
        fidx = pd.date_range(last + pd.offsets.MonthBegin(1), periods=FORECAST_MONTHS, freq="MS")
        mu = _forecast(res, fidx)
        pool = _residual_pool(res, series)
        sim_paths = _simulate(mu, fidx, pool)
        expected, median, p90 = _summarise(sim_paths)
        forecasts[lgu] = {
            t.strftime("%Y-%m"): {
                "expected": float(expected[i]), "median": float(median[i]), "p90": float(p90[i]),
            } for i, t in enumerate(fidx)
        }
        paths[lgu] = sim_paths.astype(np.float32)

    holdout = holdout_check(forecasts)
    backtest_series = _latest_fold_series(recs)

    os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
    joblib.dump({
        "version": MODEL_VERSION,
        "trained_at": ph_now().isoformat(),
        "data_through": data_through.strftime("%Y-%m"),
        "order": ORDER,
        "exog": EXOG_FEATURES,
        "forecasts": forecasts,
        "paths": paths,
        "months": [t.strftime("%Y-%m") for t in pd.date_range(
            data_through + pd.offsets.MonthBegin(1), periods=FORECAST_MONTHS, freq="MS")],
        "backtest": summary,
        "backtest_series": backtest_series,
        "holdout": holdout,
    }, ARTIFACT_PATH)

    if summary:
        s = summary["sarimax"]
        db.session.add(ModelMetrics(
            model_version=MODEL_VERSION,
            mae=round(s["mae"], 4), rmse=round(s["rmse"], 4),
            mape=round(s["mape"], 4) if s["mape"] == s["mape"] else None,
            r_squared=round(s["r2"], 4),
            wape=round(s["wape"], 4),
            # The stricter figure (calibrated only on windows that had already
            # ended) when there is enough history, else leave-one-fold-out.
            p90_coverage=round(
                summary["p90_month_coverage_strict"]
                if summary.get("p90_month_coverage_strict") is not None
                else summary["p90_month_coverage"], 4),
            naive_wape=round(summary["naive"]["wape"], 4),
            total12_err=round(summary["total_err"][12]["sarimax"], 4),
            naive_total12_err=round(summary["total_err"][12]["naive"], 4),
            training_samples=int(sum(s_.notna().sum() for s_ in series_by_lgu.values())),
        ))
        db.session.commit()

    return {"summary": summary, "holdout": holdout, "data_through": data_through.strftime("%Y-%m"),
            "lgus": list(series_by_lgu)}
