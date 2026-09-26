"""
Smoke checks for the SARIMAX forecaster and its data. This project has no
test suite; run this after training / reseeding to catch a broken model
before it reaches a page.

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
    n_b = Barangay.query.count()
    counts = dict(db.session.execute(text(
        "SELECT data_source, COUNT(*) FROM barangay_monthly_history GROUP BY 1")).fetchall())
    check("every barangay has 60 months of history (synthetic + real)",
          counts.get("synthetic", 0) + counts.get("real", 0) == n_b * 60,
          f"{counts.get('synthetic', 0)} synthetic + {counts.get('real', 0)} real vs {n_b * 60}")
    real_months = dict(db.session.execute(text(
        "SELECT DATE_FORMAT(month_start, '%Y-%m'), SUM(food_packs) FROM barangay_monthly_history "
        "WHERE data_source = 'real' GROUP BY 1")).fetchall())
    expected_real = {"2025-07": 2704, "2025-09": 5731, "2025-10": 12424, "2025-11": 950}
    check("real Urdaneta 2025 reports loaded (Jul 2,704 / Sep 5,731 / Oct 12,424 / Nov 950 packs)",
          {k: int(v) for k, v in real_months.items()} == expected_real, str(real_months))
    real = db.session.execute(text(
        "SELECT SUM(food_packs) FROM barangay_monthly_history WHERE data_source='real_sample'")).scalar()
    check("real Aug 2026 Sta. Barbara sheet loaded (14,071 packs)", int(real or 0) == 14071, str(real))
    check("no negative packs", db.session.execute(text(
        "SELECT COUNT(*) FROM barangay_monthly_history WHERE food_packs < 0")).scalar() == 0)
    check("Urdaneta uses real PSA population (145,935)", int(db.session.execute(text(
        "SELECT SUM(population) FROM barangays WHERE city_municipality='Urdaneta City'")).scalar()) == 145935)

    print("Model")
    from app.ml.train import load_lgu_series
    series_by_lgu = load_lgu_series()
    check("artifact loads", P.is_model_available())
    for lgu in ("Urdaneta City", "Santa Barbara", "Calasiao"):
        for h in (4, 6, 12):
            f = P.forecast_lgu(lgu, h)
            ok = (f is not None and len(f["months"]) == h
                  and all(m["projected_packs"] >= 0 and m["p90_packs"] >= m["projected_packs"] for m in f["months"])
                  and f["horizon_p90"] >= f["horizon_total"]
                  and f["horizon_total"] == sum(m["projected_packs"] for m in f["months"]))
            check(f"{lgu} {h}-month forecast is non-negative, P90 >= expected", ok)
        # Guard against the failure mode that once inflated expected demand 20x:
        # the next-12-month expected total must sit near what the history shows.
        annual = series_by_lgu[lgu].groupby(series_by_lgu[lgu].index.year).sum()
        exp12 = P.forecast_lgu(lgu, 12)["horizon_total"]
        check(f"{lgu}: 12-month expected is within 0.5x-2x of the average past year",
              0.5 * annual.mean() <= exp12 <= 2.0 * annual.mean(),
              f"{exp12:,} vs average year {annual.mean():,.0f} (largest {annual.max():,.0f})")
        wet = [m["projected_packs"] for m in P.forecast_lgu(lgu, 12)["months"] if m["is_peak_season"]]
        dry = [m["projected_packs"] for m in P.forecast_lgu(lgu, 12)["months"] if not m["is_wet_season"]]
        check(f"{lgu}: peak-season months forecast well above dry months",
              min(wet) > 3 * max(dry), f"min peak {min(wet):,} vs max dry {max(dry):,}")

        barangays = Barangay.query.filter_by(city_municipality=lgu).all()
        shares = P._lgu_shares(lgu)
        check(f"{lgu}: barangay shares sum to 1", abs(sum(shares.values()) - 1) < 1e-6)
        lgu_total = P.forecast_lgu(lgu, 12)["horizon_total"]
        b_total = sum(P.forecast_barangay(b, 12)["horizon_total"] for b in barangays)
        check(f"{lgu}: barangay forecasts add up to the LGU forecast (rounding only)",
              abs(b_total - lgu_total) <= len(barangays), f"{b_total:,} vs {lgu_total:,}")

    print("Metrics")
    m = db.session.execute(text(
        "SELECT model_version, p90_coverage, total12_err, naive_total12_err "
        "FROM model_metrics ORDER BY metric_id DESC LIMIT 1")).fetchone()
    check("latest metrics row is from the SARIMAX model", m is not None and str(m[0]).startswith("v8"), str(m))
    if m and m[1] is not None:
        # Wide on purpose: this catches a broken interval, it is not a claim of accuracy.
        check("P90 monthly coverage within 0.60-0.97", 0.60 <= float(m[1]) <= 0.97, f"{float(m[1]):.2f}")
    if m and m[2] is not None:
        check("12-month total error is not worse than 1.5x seasonal-naive", float(m[2]) <= 1.5 * float(m[3]),
              f"{float(m[2]):.2f} vs {float(m[3]):.2f} (informational: the model does not currently beat it)")

print("\nALL CHECKS PASSED" if not failures else f"\n{len(failures)} CHECK(S) FAILED: {failures}")
sys.exit(1 if failures else 0)
