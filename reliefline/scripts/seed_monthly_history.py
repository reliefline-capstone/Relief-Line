"""
Builds the monthly food-pack history (Jan 2021 - Aug 2026) that the SARIMAX
forecaster trains on. It is a MIX of real and synthetic data, until real
records cover everything:

  REAL       Urdaneta City, Jul / Sep / Oct / Nov 2025 - the four CSWDO event
             reports (scripts/real_urdaneta_reports_2025.py), and Calasiao,
             Jul / Sep 2025 - the Crising/Emong and Nando/Opong reports
             (scripts/real_calasiao_reports_2025.py; Jul packs are estimated,
             Sep packs measured), loaded per barangay as data_source='real'.
             Sta. Barbara, Aug 2026 - the DSWD + LGU relief-distribution sheet
             (scripts/sample_sta_barbara_aug2026.py), also data_source='real'.
             It is supply, not measured need; it is the only real Sta. Barbara
             record, so it trains the model (the rolling backtest still scores
             the forecast of that month before it is seen).
  SYNTHETIC  everything else (incl. Jan-Jul 2026, baseline incidents only -
             no verified 2026 storm calendar), anchored to reality in three ways:

  1. TIMING - demand spikes fall in the months of the real storms/monsoon
     floods that hit Pangasinan (app.ml.climate_reference.EVENTS), not
     invented events.
  2. SEASONALITY - rainfall normals (PAGASA Dagupan), wet season and ONI come
     from real sources (same module).
  3. SCALE / SHAPE - calibrated to two real sources: the Sta. Barbara
     relief-distribution sheet of Aug 2026 (a severe event: ~14,000 packs,
     ~83% of barangays reached, median ~550 packs per reached barangay) and
     the four Urdaneta 2025 reports (mild to severe: reach 82-91%, 0.02-0.31
     packs per household, LGU relief capped near 500 packs per barangay).
     `--report` prints how close the generator gets to each.

Severity is PER LGU (climate_reference.severity_for): one storm hit Urdaneta
and Calasiao very differently, which the real reports showed clearly.

How a barangay-month is produced
  per event -> barangay reach probability (severity + flood susceptibility)
            -> packs = households x rate(severity) x hazard multiplier
                       x LGU factor x lognormal noise
            -> spread over the delivery window (event start+2d .. end+12d),
               so a late-month storm spills into the next month, as in the
               sheet (received 19 Aug - 2 Sep)
  plus a small baseline of localized incidents in ordinary months.

Also: assigns the barangay flood-hazard attributes (flood_susceptibility,
river_proximity_km, elevation_m) - from the real reports for Urdaneta and the
Sta. Barbara sheet for Sta. Barbara, synthetic for Calasiao - and loads the
real Aug 2026 Sta. Barbara sheet as data_source='real'.

Deterministic (seeded per barangay+event) and idempotent: re-running replaces
the 'synthetic' and 'real' rows from their sources and leaves any 'system' rows alone.

    .venv/Scripts/python.exe -m scripts.seed_monthly_history            # seed
    .venv/Scripts/python.exe -m scripts.seed_monthly_history --report   # calibration only
    bash scripts/sync_db_dump.sh
"""
import math
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.ml import climate_reference as ref
from app.models.barangay import Barangay
from scripts import real_calasiao_reports_2025 as calasiao_real
from scripts import real_urdaneta_reports_2025 as urdaneta_real
from scripts import sample_sta_barbara_aug2026 as sample
from scripts.apply_timeseries_schema import ensure_schema

# Packs served per affected family, measured over the four Urdaneta 2025
# reports: 21,809 packs / 27,034 families = 0.81 (relief is capped and lags need).
# Used only to derive an "affected families" figure for synthetic rows.
PACKS_PER_FAMILY = 0.81

# Probability a barangay receives relief in an event of this severity.
# Urdaneta reports: 82% / 85% / 88% / 91% of barangays received packs in its
# severity 1 / 2 / 3 / 4 events (28-31 of 34); Sta. Barbara Aug 2026: 83%.
SEV_REACH = {1: 0.80, 2: 0.85, 3: 0.88, 4: 0.91, 5: 0.87}
# Packs per household when reached, before hazard / LGU multipliers.
SEV_RATE = {1: 0.05, 2: 0.10, 3: 0.22, 4: 0.55, 5: 0.62}
# LGU -> module holding its real event reports. generate_history skips these
# LGU-events; load_real replaces them.
REAL_REPORTS = {"Urdaneta City": urdaneta_real, "Calasiao": calasiao_real}
SAMPLE_EVENT = "habagat_aug2026"   # the event the Sta. Barbara sheet records
HAZARD_MULT = {1: 0.50, 2: 0.85, 3: 1.20, 4: 1.60}
# Calasiao and Sta. Barbara sit on the Marusay/Sinocalan floodplain (both
# flooded badly in Jul 2025 and Aug 2026); Urdaneta is less exposed.
LGU_REACH = {"Calasiao": 1.05, "Santa Barbara": 1.00, "Urdaneta City": 1.00}
LGU_RATE = {"Calasiao": 1.10, "Santa Barbara": 1.00, "Urdaneta City": 0.75}
# Urdaneta's LGU relief is capped at ~500 packs per barangay per event (17 of
# 31 barangays sit exactly at 500 in the Paolo report; DSWD top-ups reach 554-570).
LGU_CAP = {"Urdaneta City": 570}
# Real relief numbers are lot-sized, not exact: nearest 50 above 200, 10 above
# 50, else 5 (Urdaneta: 10/20/25/50/100/200/300/500; Sta. Barbara: 250/300/350/400).
NOISE_SIGMA = 0.55
MIN_PACKS = 5

# Synthetic hazard baselines per LGU: (susceptibility, river km, elevation m).
LGU_HAZARD = {
    "Calasiao": (3.0, 1.1, 5.0),
    "Santa Barbara": (2.7, 1.4, 9.0),
    "Urdaneta City": (2.2, 2.4, 14.0),
}


def simulate_event_packs(rng, households, susceptibility, lgu, severity):
    reach = SEV_REACH[severity] + 0.07 * (susceptibility - 2.5)
    reach = min(max(reach * LGU_REACH.get(lgu, 1.0), 0.02), 0.98)
    if rng.random() > reach:
        return 0
    noise = math.exp(rng.gauss(-NOISE_SIGMA ** 2 / 2, NOISE_SIGMA))
    packs = households * SEV_RATE[severity] * HAZARD_MULT[susceptibility] \
        * LGU_RATE.get(lgu, 1.0) * noise
    packs = min(packs, LGU_CAP.get(lgu, float("inf")))
    return max(_lot(packs), MIN_PACKS)


def _lot(packs):
    """Round to a lot-like number (see the note by LGU_CAP)."""
    unit = 50 if packs >= 200 else (10 if packs >= 50 else 5)
    return int(round(packs / unit) * unit)


def month_split(event):
    """{(year, month): fraction} of an event's relief by delivery month."""
    d0 = event["start"] + timedelta(days=2)
    d1 = event["end"] + timedelta(days=12)
    days = [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]
    counts = Counter((d.year, d.month) for d in days)
    return {k: v / len(days) for k, v in counts.items()}


# --- hazard attributes --------------------------------------------------------

def assign_hazard(barangays):
    """Sets flood_susceptibility / river_proximity_km / elevation_m.

    Real flood-impact evidence drives the two LGUs we hold it for:
      * Urdaneta - mean share of households affected across the four 2025
        CSWDO reports, split into quartiles -> class 1-4.
      * Sta. Barbara - relief per household in the Aug 2026 sheet (not reached
        -> 1, then 2/3/4 by cut points).
    Calasiao is a deterministic, LGU-shaped synthetic value. All to be
    replaced by MGB/NOAH data (hazard_source says which)."""
    totals = sample.combined_totals()
    # Urdaneta: mean share of households affected across the four real events.
    ur = [b for b in barangays if b.city_municipality == "Urdaneta City"]
    reports = [urdaneta_real.by_key(r) for r in urdaneta_real.REPORTS]
    ur_score = {}
    for b in ur:
        shares = [rep_[urdaneta_real.normalize(b.barangay_name)][0] / max(b.num_households, 1)
                  for rep_ in reports if urdaneta_real.normalize(b.barangay_name) in rep_]
        ur_score[b.barangay_id] = sum(shares) / len(shares) if shares else None
    ranked = sorted(v for v in ur_score.values() if v is not None)
    q1, q2, q3 = (ranked[len(ranked) * k // 4] for k in (1, 2, 3))
    sb = [b for b in barangays if b.city_municipality == "Santa Barbara"]
    rates = sorted(
        totals[sample.normalize(b.barangay_name)] / max(b.num_households, 1)
        for b in sb if sample.normalize(b.barangay_name) in totals
    )
    cut_lo = rates[len(rates) // 3]
    cut_hi = rates[(len(rates) * 3) // 4]

    for b in barangays:
        rng = random.Random(f"hazard|{b.city_municipality}|{b.barangay_name}")
        base_s, base_r, base_e = LGU_HAZARD[b.city_municipality]
        key = sample.normalize(b.barangay_name)
        if b.city_municipality == "Santa Barbara":
            if key not in totals:
                susc = 1
            else:
                rate = totals[key] / max(b.num_households, 1)
                susc = 2 if rate < cut_lo else (3 if rate < cut_hi else 4)
            b.hazard_source = "sample-derived"
        elif b.city_municipality == "Urdaneta City" and ur_score[b.barangay_id] is not None:
            sc = ur_score[b.barangay_id]
            susc = 1 if sc < q1 else (2 if sc < q2 else (3 if sc < q3 else 4))
            b.hazard_source = "report-derived"
        else:
            susc = int(min(max(round(rng.gauss(base_s, 0.8)), 1), 4))
            b.hazard_source = "synthetic"
        # Nearer the river / lower ground goes with higher susceptibility.
        b.flood_susceptibility = susc
        b.river_proximity_km = round(max(0.1, base_r * (1.6 - 0.35 * susc) + rng.uniform(-0.3, 0.5)), 2)
        b.elevation_m = round(max(1.0, base_e * (1.5 - 0.22 * susc) + rng.uniform(-2.0, 2.5)), 1)


# --- history generation ---------------------------------------------------------

def history_months():
    return [date(y, m, 1) for y in range(ref.HISTORY_START.year, ref.HISTORY_END.year + 1)
            for m in range(1, 13) if ref.HISTORY_START <= date(y, m, 1) <= ref.HISTORY_END]


def generate_history(barangays):
    """{(barangay_id, month_start): dict(packs, families, events, severity)}"""
    rows = defaultdict(lambda: {"packs": 0.0, "events": 0, "severity": 0})
    real_keys = {lgu: {r["key"] for r in mod.REPORTS} for lgu, mod in REAL_REPORTS.items()}
    for ev in ref.EVENTS:
        split = month_split(ev)
        for b in barangays:
            if ev["key"] in real_keys.get(b.city_municipality, ()):
                continue  # a real report exists - loaded by load_real
            if ev["key"] == SAMPLE_EVENT and b.city_municipality == "Santa Barbara":
                continue  # the real sheet exists - loaded by load_real_sample
            sev = ref.severity_for(ev, b.city_municipality)
            rng = random.Random(f"hist|{b.barangay_id}|{ev['key']}")
            packs = simulate_event_packs(
                rng, b.num_households, b.flood_susceptibility, b.city_municipality, sev)
            if packs <= 0:
                continue
            for (y, m), frac in split.items():
                cell = rows[(b.barangay_id, date(y, m, 1))]
                cell["packs"] += packs * frac
                cell["events"] += 1
                cell["severity"] = max(cell["severity"], sev)

    # Baseline localized incidents in any month.
    months = history_months()
    for b in barangays:
        for ms in months:
            rng = random.Random(f"base|{b.barangay_id}|{ms.isoformat()}")
            if rng.random() < ref.BASELINE_INCIDENT_PROB:
                rows[(b.barangay_id, ms)]["packs"] += rng.randint(*ref.BASELINE_INCIDENT_PACKS)

    out = {}
    for (bid, ms), c in rows.items():
        if ms > ref.HISTORY_END:
            continue  # spill past the last history month is dropped
        packs = int(round(c["packs"]))
        out[(bid, ms)] = {
            "packs": packs,
            "families": int(round(packs / PACKS_PER_FAMILY)),
            "events": c["events"],
            "severity": c["severity"],
        }
    return out, months


def climate_rows(months):
    rows = []
    by_month = defaultdict(lambda: (0, 0))
    for ev in ref.EVENTS:
        for (y, m) in month_split(ev):
            n, s = by_month[date(y, m, 1)]
            by_month[date(y, m, 1)] = (n + 1, max(s, ev["severity"]))
    for ms in months:
        rng = random.Random(f"climate|{ms.isoformat()}")
        normal = ref.RAINFALL_NORMAL_MM[ms.month - 1]
        n_ev, sev = by_month.get(ms, (0, 0))
        if sev:
            factor = (1 + 0.18 * sev) * math.exp(rng.gauss(0, 0.12))
        else:
            sigma = 0.35 if ms.month in ref.WET_SEASON_MONTHS else 0.6
            factor = math.exp(rng.gauss(-sigma ** 2 / 2, sigma))
        rows.append({
            "month_start": ms, "rainfall_normal_mm": normal,
            "rainfall_mm": round(normal * factor, 1),
            "oni": ref.oni_for(ms.year, ms.month),
            "event_count": n_ev, "max_event_severity": sev,
        })
    return rows


# --- calibration against the real sheet -------------------------------------------

def calibration_report(barangays, replications=300):
    """Simulate one severity-5 event over Sta. Barbara many times and compare
    with the real Aug 2026 sheet."""
    sb = [b for b in barangays if b.city_municipality == "Santa Barbara"]
    real = sample.combined_totals()
    real_vals = sorted(real.values())
    real_total = sum(real_vals)
    real_reach = len(real) / len(sb)

    totals, reaches, medians, p90s, maxes = [], [], [], [], []
    for r in range(replications):
        vals = []
        for b in sb:
            rng = random.Random(f"calib|{r}|{b.barangay_id}")
            v = simulate_event_packs(rng, b.num_households, b.flood_susceptibility, "Santa Barbara", 5)
            if v > 0:
                vals.append(v)
        vals.sort()
        totals.append(sum(vals))
        reaches.append(len(vals) / len(sb))
        if vals:
            medians.append(vals[len(vals) // 2])
            p90s.append(vals[int(len(vals) * 0.9) - 1])
            maxes.append(vals[-1])

    def row(label, sim, actual, tol):
        ok = abs(sim - actual) / actual <= tol
        print(f"  {label:<34}{sim:>12,.2f}{actual:>12,.2f}   {'OK' if ok else 'CHECK'} (+/-{int(tol * 100)}%)")
        return ok

    print("Calibration: severity-5 event, Sta. Barbara (mean of "
          f"{replications} runs) vs real Aug 2026 sheet")
    print(f"  {'metric':<34}{'simulated':>12}{'real sheet':>12}")
    checks = [
        row("municipal total packs", statistics.mean(totals), real_total, 0.15),
        row("share of barangays reached", statistics.mean(reaches), real_reach, 0.12),
        row("median packs per reached barangay", statistics.mean(medians), real_vals[len(real_vals) // 2], 0.20),
        row("p90 packs per reached barangay", statistics.mean(p90s), real_vals[int(len(real_vals) * 0.9) - 1], 0.25),
    ]
    return all(checks)


# --- persistence --------------------------------------------------------------------

def persist(barangays, history, months, climate):
    lo, hi = ref.HISTORY_START, ref.HISTORY_END
    db.session.execute(text(
        "DELETE FROM barangay_monthly_history WHERE data_source IN ('synthetic', 'real', 'real_sample') "
        "AND month_start BETWEEN :lo AND :hi"), {"lo": lo, "hi": hi})
    db.session.execute(text("DELETE FROM climate_monthly WHERE month_start BETWEEN :lo AND :hi"),
                       {"lo": lo, "hi": hi})

    # A row for EVERY barangay-month (zeros included) so the series has no gaps.
    batch = []
    for b in barangays:
        for ms in months:
            h = history.get((b.barangay_id, ms), {"packs": 0, "families": 0, "events": 0, "severity": 0})
            batch.append({"b": b.barangay_id, "m": ms, "p": h["packs"], "f": h["families"],
                          "e": h["events"], "s": h["severity"]})
    db.session.execute(text(
        "INSERT INTO barangay_monthly_history (barangay_id, month_start, food_packs, "
        "affected_families, event_count, max_event_severity, data_source) "
        "VALUES (:b, :m, :p, :f, :e, :s, 'synthetic')"), batch)

    db.session.execute(text(
        "INSERT INTO climate_monthly (month_start, rainfall_normal_mm, rainfall_mm, oni, "
        "event_count, max_event_severity) VALUES (:month_start, :rainfall_normal_mm, "
        ":rainfall_mm, :oni, :event_count, :max_event_severity)"), climate)
    db.session.commit()


def load_real_sample(barangays):
    """The Aug 2026 Sta. Barbara sheet -> history rows (data_source='real')."""
    month = date(2026, 8, 1)
    totals = sample.combined_totals()
    sb = [b for b in barangays if b.city_municipality == "Santa Barbara"]
    unmatched = set(totals) - {sample.normalize(b.barangay_name) for b in sb}
    if unmatched:
        raise RuntimeError(f"Sheet barangays not found in the barangays table: {sorted(unmatched)}")
    db.session.execute(text(
        "DELETE FROM barangay_monthly_history WHERE data_source IN ('real', 'real_sample') AND month_start=:m "
        "AND barangay_id IN (SELECT barangay_id FROM barangays WHERE city_municipality = 'Santa Barbara')"),
        {"m": month})
    batch = []
    for b in sb:
        packs = totals.get(sample.normalize(b.barangay_name), 0)
        batch.append({"b": b.barangay_id, "m": month, "p": packs, "f": int(round(packs / PACKS_PER_FAMILY))})
    db.session.execute(text(
        "INSERT INTO barangay_monthly_history (barangay_id, month_start, food_packs, "
        "affected_families, event_count, max_event_severity, data_source) "
        "VALUES (:b, :m, :p, :f, 1, 5, 'real') "
        "ON DUPLICATE KEY UPDATE food_packs=VALUES(food_packs), "
        "affected_families=VALUES(affected_families), event_count=1, max_event_severity=5, data_source='real'"), batch)
    db.session.commit()
    return len(batch), sum(x["p"] for x in batch)


def load_real(barangays, lgu, module):
    """An LGU's real event reports -> history rows (data_source='real').
    Every barangay of the LGU gets a row per event month: its reported packs /
    families, or 0 where the report has no entry (not reported)."""
    own = [b for b in barangays if b.city_municipality == lgu]
    known = {module.normalize(b.barangay_name) for b in own}
    total_packs = 0
    for report in module.REPORTS:
        rows = module.by_key(report)
        unmatched = set(rows) - known
        if unmatched:
            raise RuntimeError(f"Report '{report['short']}' has barangays not in the table: {sorted(unmatched)}")
        ev = next(e for e in ref.EVENTS if e["key"] == report["key"])
        sev = ref.severity_for(ev, lgu)
        month = date.fromisoformat(report["month"])
        batch = []
        for b in own:
            fam, _persons, packs = rows.get(module.normalize(b.barangay_name), (0, 0, 0))
            batch.append({"b": b.barangay_id, "m": month, "p": packs, "f": fam, "s": sev})
            total_packs += packs
        db.session.execute(text(
            "INSERT INTO barangay_monthly_history (barangay_id, month_start, food_packs, "
            "affected_families, event_count, max_event_severity, data_source) "
            "VALUES (:b, :m, :p, :f, 1, :s, 'real') "
            "ON DUPLICATE KEY UPDATE food_packs=VALUES(food_packs), affected_families=VALUES(affected_families), "
            "event_count=1, max_event_severity=VALUES(max_event_severity), data_source='real'"), batch)
    db.session.commit()
    return len(module.REPORTS) * len(own), total_packs


def calibration_urdaneta(barangays, replications=300):
    """Simulate each real Urdaneta event at the severity assigned to it and
    compare with the real report (packs, reach, median and p90 per reached
    barangay). Hazard classes are derived from the same reports, so this is a
    calibration check, not independent validation."""
    ur = [b for b in barangays if b.city_municipality == "Urdaneta City"]
    print("\nCalibration: Urdaneta City real 2025 events vs simulation at the assigned severity "
          f"(mean of {replications} runs)")
    print(f"  {'event (severity)':<30}{'metric':<9}{'simulated':>11}{'real':>9}   ")
    ok_all = True
    for report in urdaneta_real.REPORTS:
        ev = next(e for e in ref.EVENTS if e["key"] == report["key"])
        sev = ref.severity_for(ev, "Urdaneta City")
        real = urdaneta_real.stats_of(report, len(ur))
        tot, reach, med, p90 = [], [], [], []
        for r in range(replications):
            vals = []
            for b in ur:
                rng = random.Random(f"calibU|{r}|{b.barangay_id}|{report['key']}")
                v = simulate_event_packs(rng, b.num_households, b.flood_susceptibility, "Urdaneta City", sev)
                if v > 0:
                    vals.append(v)
            vals.sort()
            tot.append(sum(vals)); reach.append(len(vals) / len(ur))
            if vals:
                med.append(vals[len(vals) // 2]); p90.append(vals[max(int(len(vals) * 0.9) - 1, 0)])
        for label, sim, act, tol in (("packs", statistics.mean(tot), real["packs"], 0.25),
                                     ("reach", statistics.mean(reach), real["reach"], 0.12),
                                     ("median", statistics.mean(med), real["median"], 0.45),
                                     ("p90", statistics.mean(p90), real["p90"], 0.40)):
            good = abs(sim - act) / max(act, 1) <= tol
            ok_all &= good
            print(f"  {report['short'] + f' (sev {sev})':<30}{label:<9}{sim:>11,.2f}{act:>9,.2f}   "
                  f"{'OK' if good else 'CHECK'} (+/-{int(tol * 100)}%)")
    return ok_all


def summary(barangays, history):
    print("\nSynthetic history summary (packs per LGU; the real 2025 months are loaded separately and not counted here)")
    lgu_of = {b.barangay_id: b.city_municipality for b in barangays}
    monthly = defaultdict(int)
    for (bid, ms), h in history.items():
        monthly[(lgu_of[bid], ms)] += h["packs"]
    for lgu in sorted(LGU_REACH):
        by_year = defaultdict(int)
        peak = max(((v, k[1]) for k, v in monthly.items() if k[0] == lgu), default=(0, None))
        for (l, ms), v in monthly.items():
            if l == lgu:
                by_year[ms.year] += v
        years = "  ".join(f"{y}: {by_year[y]:>7,}" for y in range(2021, 2027))
        print(f"  {lgu:<14}{years}   peak month {peak[1]:%b %Y} = {peak[0]:,}")


def main(report_only=False):
    ensure_schema()
    barangays = Barangay.query.order_by(Barangay.barangay_id).all()
    assign_hazard(barangays)
    if report_only:
        calibration_report(barangays)
        calibration_urdaneta(barangays)
        return
    db.session.commit()

    history, months = generate_history(barangays)
    persist(barangays, history, months, climate_rows(months))
    loaded = {lgu: load_real(barangays, lgu, mod) for lgu, mod in REAL_REPORTS.items()}
    n, total = load_real_sample(barangays)
    ok = calibration_report(barangays)
    ok &= calibration_urdaneta(barangays)
    summary(barangays, history)
    for lgu, (n_real, packs_real) in loaded.items():
        print(f"\nLoaded real {lgu} 2025 reports: {n_real} barangay-months, {packs_real:,} packs (data_source='real')")
    print(f"Loaded real Aug 2026 Sta. Barbara sample: {n} barangays, {total:,} packs (data_source='real')")
    print("Calibration: " + ("all checks within tolerance" if ok else "some checks outside tolerance - see the CHECK lines above"))


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        main(report_only="--report" in sys.argv)
