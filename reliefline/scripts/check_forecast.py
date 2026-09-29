"""
Smoke checks for the two-stage forecaster and its real relief data. This
project has no test suite; run this after loading new relief data / training
to catch a broken model before it reaches a page.

    .venv/Scripts/python.exe -m scripts.check_forecast

Exits non-zero if any check fails.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.ml import predict as P
from app.models.barangay import Barangay

failures = []


def check(name, cond, detail=""):
    print(f"  [{'ok' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not cond:
        failures.append(name)


app = create_app()
with app.app_context():
    print("Data")
    check("typhoon_calendar has 36 verified events",
          db.session.execute(text("SELECT COUNT(*) FROM typhoon_calendar")).scalar() == 36)
    n_ref_events = db.session.execute(text(
        "SELECT COUNT(*) FROM disaster_events WHERE is_reference = 1")).scalar()
    check("disaster_events has a matching is_reference row per calendar typhoon", n_ref_events == 36,
          str(n_ref_events))
    n_unlinked = db.session.execute(text(
        "SELECT COUNT(*) FROM typhoon_calendar WHERE disaster_event_id IS NULL")).scalar()
    check("every typhoon_calendar row resolves to a disaster_events row", n_unlinked == 0, str(n_unlinked))

    per_lgu = dict(db.session.execute(text(
        "SELECT city_municipality, COUNT(*) FROM relief_events GROUP BY 1")).fetchall())
    check("Calasiao has real relief events on record", per_lgu.get("Calasiao", 0) >= 20, str(per_lgu))
    check("Santa Barbara has real relief events on record", per_lgu.get("Santa Barbara", 0) >= 5, str(per_lgu))
    check("Urdaneta City has real relief events on record", per_lgu.get("Urdaneta City", 0) >= 10, str(per_lgu))

    n_neg = db.session.execute(text(
        "SELECT COUNT(*) FROM barangay_relief_records WHERE food_packs_given < 0 "
        "OR affected_families < 0 OR total_families_snapshot < 0")).scalar()
    check("no negative values in barangay_relief_records", n_neg == 0, str(n_neg))

    sb_aug2026 = db.session.execute(text(
        "SELECT SUM(r.food_packs_given) FROM barangay_relief_records r "
        "JOIN relief_events e ON e.relief_event_id = r.relief_event_id "
        "WHERE e.city_municipality = 'Santa Barbara' AND e.label LIKE 'Aug 2026%'")).scalar()
    check("real Aug 2026 Sta. Barbara sheet loaded (14,071 packs)", int(sb_aug2026 or 0) == 14071, str(sb_aug2026))

    # All three LGUs now source population/num_households from the latest
    # real relief record (not PSA, not synthetic) - see scripts/real_profiles.py.
    check("Calasiao uses real relief-record population (not synthetic)", int(db.session.execute(text(
        "SELECT SUM(population) FROM barangays WHERE city_municipality='Calasiao'")).scalar()) == 116239)
    check("Santa Barbara uses real relief-record population (not synthetic)", int(db.session.execute(text(
        "SELECT SUM(population) FROM barangays WHERE city_municipality='Santa Barbara'")).scalar()) == 87680)
    check("Urdaneta uses real relief-record population (Maymay 2026, not PSA anymore)", int(db.session.execute(text(
        "SELECT SUM(population) FROM barangays WHERE city_municipality='Urdaneta City'")).scalar()) == 145935)
    check("Urdaneta uses real relief-record family count (Maymay 2026, not PSA households)",
          int(db.session.execute(text(
              "SELECT SUM(num_households) FROM barangays WHERE city_municipality='Urdaneta City'")).scalar()) == 35594)

    n_synthetic_tables = db.session.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() "
        "AND table_name IN ('barangay_monthly_history', 'climate_monthly')")).scalar()
    check("synthetic-history tables are gone", n_synthetic_tables == 0, f"{n_synthetic_tables} still present")

    print("Model")
    check("artifact loads", P.is_model_available())
    for lgu in ("Urdaneta City", "Santa Barbara", "Calasiao"):
        for h in (3, 6, 12):
            f = P.forecast_lgu(lgu, h)
            ok = (f is not None and len(f["months"]) == h
                  and all(m["projected_packs"] >= 0 and m["p90_packs"] >= m["projected_packs"] for m in f["months"])
                  and f["horizon_p90"] >= f["horizon_total"]
                  and f["horizon_total"] == sum(m["projected_packs"] for m in f["months"]))
            check(f"{lgu} {h}-month forecast is non-negative, P90 >= expected", ok)

        barangays = Barangay.query.filter_by(city_municipality=lgu).all()
        shares = P._lgu_shares(lgu)
        check(f"{lgu}: barangay shares sum to 1", abs(sum(shares.values()) - 1) < 1e-6,
              f"{sum(shares.values()):.6f}")
        lgu_total = P.forecast_lgu(lgu, 12)["horizon_total"]
        b_total = sum(P.forecast_barangay(b, 12)["horizon_total"] for b in barangays)
        check(f"{lgu}: barangay forecasts add up to the LGU forecast (rounding only)",
              abs(b_total - lgu_total) <= len(barangays), f"{b_total:,} vs {lgu_total:,}")

        bt = P.backtest_series(lgu)
        check(f"{lgu}: leave-one-typhoon-out backtest series available", bt is not None and len(bt["points"]) > 0,
              str(len(bt["points"])) if bt else "none")

    print("Validation (leave-one-typhoon-out vs. baselines)")
    from app.ml.train import load_relief_data, _share_training_rows, fit_share_model, leave_one_typhoon_out_cv
    by_lgu = load_relief_data()
    for lgu, events in by_lgu.items():
        cv = leave_one_typhoon_out_cv(events)
        if cv is None:
            check(f"{lgu}: LOTO-CV ran", False, "not enough events to validate")
            continue
        # Wide/informational check on purpose: equal-split is a very weak
        # baseline (see app.ml.train module doc), so this mainly guards
        # against a badly broken fit, not a claim of beating every baseline.
        check(f"{lgu}: share model beats equal-split baseline (MAE {cv['mae_model']:.4f} vs {cv['mae_equal_split']:.4f})",
              cv["mae_model"] <= cv["mae_equal_split"])

    print("Validation (leave-one-typhoon-out P90 coverage, target ~90%)")
    from app.ml.train import leave_one_typhoon_out_p90_coverage
    for lgu, events in by_lgu.items():
        p90 = leave_one_typhoon_out_p90_coverage(events)
        if p90 is None:
            check(f"{lgu}: P90 coverage check ran", False, "not enough events to validate")
            continue
        # Wide on purpose - this catches a badly broken P90 (e.g. barely
        # above 0 or always 100%), not a precise claim of hitting 90% with
        # this few events per LGU (see the module's own caveat on n).
        check(f"{lgu}: barangay-level P90 coverage within 0.60-1.00 "
              f"({p90['barangay_coverage']*100:.1f}%, {p90['barangay_n']} pairs)",
              0.60 <= p90["barangay_coverage"] <= 1.00)

    print("Metrics")
    m = db.session.execute(text(
        "SELECT model_version, mae, mae_baseline_equal_split, mae_baseline_avg_share "
        "FROM model_metrics ORDER BY metric_id DESC LIMIT 1")).fetchone()
    check("latest metrics row is from the two-stage model", m is not None and str(m[0]).startswith("v9"), str(m))

print("\nALL CHECKS PASSED" if not failures else f"\n{len(failures)} CHECK(S) FAILED: {failures}")
sys.exit(1 if failures else 0)
