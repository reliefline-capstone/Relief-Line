"""
Smoke checks for the two-stage forecaster and its real relief data. This
project has no test suite; run this after loading new relief data / training
to catch a broken model before it reaches a page.

    .venv/Scripts/python.exe -m scripts.check_forecast

Exits non-zero if any check fails. A [WARN] line is a known limitation or
a below-target figure worth reading - it is printed loudly but does not
fail the run (e.g. Calasiao's 12-month P90 knowingly sits below its largest
storm on record).
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
warnings = []

# LGUs whose 12-month P90 is KNOWN to sit below their largest real event (a
# once-in-years storm no forecast from 8-14 events covers) - a warning there,
# a failure anywhere else.
KNOWN_UNCOVERED_LARGEST_EVENT = {"Calasiao"}

# Does the 15% safety buffer count as covering the largest storm? A POLICY
# decision, not a modelling one - so it's an explicit switch, not a silent
# choice. While False, an LGU covered only thanks to the buffer is a WARN.
BUFFER_COUNTS_AS_COVERAGE = False


def check(name, cond, detail=""):
    print(f"  [{'ok' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def warn_unless(name, cond, detail=""):
    print(f"  [{'ok' if cond else 'WARN'}] {name}" + (f" - {detail}" if detail else ""))
    if not cond:
        warnings.append(name)


def info(text_):
    print(f"  [info] {text_}")


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
    check("Calasiao has real relief events on record", per_lgu.get("Calasiao", 0) >= 10, str(per_lgu))
    check("Santa Barbara has real relief events on record", per_lgu.get("Santa Barbara", 0) >= 5, str(per_lgu))
    check("Urdaneta City has real relief events on record", per_lgu.get("Urdaneta City", 0) >= 10, str(per_lgu))

    # Only real typhoon reports may train the model: every relief event must
    # link to at least one verified typhoon_calendar key. Keeps app test rows
    # ("Test Typhoon", "try lang", ...) out if they're ever ingested.
    unlinked = db.session.execute(text(
        "SELECT e.relief_event_id, e.city_municipality, e.label FROM relief_events e "
        "WHERE NOT EXISTS (SELECT 1 FROM relief_event_typhoons t "
        "                  JOIN typhoon_calendar c ON c.typhoon_key = t.typhoon_key "
        "                  WHERE t.relief_event_id = e.relief_event_id)")).fetchall()
    check("every relief event links to a verified typhoon_calendar storm (no test/unlinked events)",
          not unlinked, str([tuple(r) for r in unlinked][:5]))

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
    # Expected sums come from scripts/real_profiles.py itself (not hard-coded),
    # so a dataset update only needs apply_real_profiles.py re-run, not an
    # edit here.
    from scripts.real_profiles import REAL_PROFILES
    for lgu in ("Calasiao", "Santa Barbara", "Urdaneta City"):
        for field in ("population", "num_households"):
            expected = sum(v[field] for (city, _n), v in REAL_PROFILES.items() if city == lgu and field in v)
            actual = int(db.session.execute(text(
                f"SELECT SUM({field}) FROM barangays WHERE city_municipality = :lgu"), {"lgu": lgu}).scalar() or 0)
            check(f"{lgu} {field} matches real relief-record figures (real_profiles.py)",
                  expected > 0 and actual == expected, f"{actual:,} vs {expected:,}")

    n_synthetic_tables = db.session.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() "
        "AND table_name IN ('barangay_monthly_history', 'climate_monthly')")).scalar()
    check("synthetic-history tables are gone", n_synthetic_tables == 0, f"{n_synthetic_tables} still present")

    print("Model")
    check("artifact loads", P.is_model_available())
    from app.ml.train import MODEL_VERSION
    art = P._load_artifact()
    check("artifact was trained by the current code (version matches MODEL_VERSION)",
          art is not None and art.get("version") == MODEL_VERSION,
          f"{art.get('version') if art else None} vs {MODEL_VERSION}")

    n_calendar = db.session.execute(text("SELECT COUNT(*) FROM typhoon_calendar")).scalar()
    event_totals = db.session.execute(text(
        "SELECT e.relief_event_id, e.city_municipality, COALESCE(SUM(r.food_packs_given), 0) "
        "FROM relief_events e LEFT JOIN barangay_relief_records r ON r.relief_event_id = e.relief_event_id "
        "GROUP BY e.relief_event_id, e.city_municipality")).fetchall()
    for lgu in ("Urdaneta City", "Santa Barbara", "Calasiao"):
        L = (art or {}).get("lgu", {}).get(lgu)
        if L is None:
            check(f"{lgu}: in the artifact", False)
            continue
        db_ids = sorted(eid for eid, city, _t in event_totals if city == lgu)
        check(f"{lgu}: artifact was trained on the events now in the database (not stale)",
              L.get("event_ids") == db_ids, f"artifact {len(L.get('event_ids') or [])} vs database {len(db_ids)} events")
        n_rec, packs = db.session.execute(text(
            "SELECT COUNT(*), COALESCE(SUM(r.food_packs_given), 0) FROM barangay_relief_records r "
            "JOIN relief_events e ON e.relief_event_id = r.relief_event_id WHERE e.city_municipality = :lgu"),
            {"lgu": lgu}).fetchone()
        check(f"{lgu}: artifact matches the database's records and pack total (no edits since training)",
              L.get("n_records") == n_rec and L.get("total_packs") == int(packs),
              f"artifact {L.get('n_records')} records / {L.get('total_packs')} packs vs database {n_rec} / {int(packs)}")
        # P(relief) recomputed straight from the database: relief events
        # with packs, linked to a calendar storm, per calendar storm.
        with_packs = [float(tot) for eid, city, tot in event_totals if city == lgu and tot > 0]
        p_db = len(with_packs) / n_calendar
        check(f"{lgu}: P(relief) = relief events with packs / calendar storms "
              f"({len(with_packs)}/{n_calendar} = {p_db:.3f})",
              abs(L["p_relief"] - p_db) < 1e-9, f"artifact {L['p_relief']:.3f}")
        # NOT a validation - true by construction once P(relief) is events /
        # storms. It only catches a wrong or stale artifact.
        implied = n_calendar * L["p_relief"] * L["severity"]["expected"]
        check(f"{lgu}: artifact consistency - storms x P(relief) x mean event size = real total",
              abs(implied - sum(with_packs)) < 1, f"{implied:,.0f} vs {sum(with_packs):,.0f}")
        f12 = P.forecast_lgu(lgu, 12)
        largest = int(max(with_packs)) if with_packs else 0
        unbuffered, buffered = f12["p90_before_buffer"], f12["horizon_p90"]
        msg = f"12-month P90 {unbuffered:,} before buffer / {buffered:,} with buffer vs largest event {largest:,}"
        if unbuffered >= largest:
            check(f"{lgu}: 12-month P90 covers its largest real event", True, msg)
        elif buffered >= largest:
            # Covered only by the buffer - a policy call (see the switch above).
            (check if BUFFER_COUNTS_AS_COVERAGE else warn_unless)(
                f"{lgu}: 12-month P90 covers its largest real event only via the safety buffer",
                BUFFER_COUNTS_AS_COVERAGE, msg)
        elif lgu in KNOWN_UNCOVERED_LARGEST_EVENT:
            warn_unless(f"{lgu}: 12-month P90 covers its largest real event (known limit)", False, msg)
        else:
            check(f"{lgu}: 12-month P90 covers its largest real event", False, msg)
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
    from app.ml.train import load_relief_data, leave_one_typhoon_out_cv, pooled_history_shares, _is_supply_only
    from app.ml.train import _event_total_and_known
    by_lgu = load_relief_data()
    for lgu, events in by_lgu.items():
        cv = leave_one_typhoon_out_cv(events)
        if cv is None:
            check(f"{lgu}: LOTO-CV ran", False, "not enough events to validate")
            continue
        # Equal-split is the weakest baseline: this only guards against a
        # badly broken fit.
        check(f"{lgu}: share model beats equal-split baseline (MAE {cv['mae_model']:.4f} vs {cv['mae_equal_split']:.4f})",
              cv["mae_model"] <= cv["mae_equal_split"])
        # Pooled history is the real bar - informational, since the model
        # does not clearly beat it (see app.ml.train module doc).
        lo, hi = cv["diff_vs_pooled_weighted_ci"]
        info(f"{lgu}: vs pooled history (size-weighted) {cv['mae_model_weighted']:.4f} vs "
             f"{cv['mae_pooled_history_weighted']:.4f}; better in {cv['beats_pooled_k']} of "
             f"{cv['beats_pooled_n']} storms; 95% interval {lo:+.4f} to {hi:+.4f}"
             + (" (no clear difference)" if lo < 0 < hi else ""))
        # Supply-only sheets (no family counts, e.g. Sta. Barbara's event 49)
        # must never feed history shares - guards a future reload.
        supply = [eid for eid, ev in events.items() if _is_supply_only(_event_total_and_known(ev["records"])[1])]
        without = {eid: ev for eid, ev in events.items() if eid not in supply}
        check(f"{lgu}: pooled history ignores supply-only events ({len(supply)} found)",
              pooled_history_shares(events) == pooled_history_shares(without))

    print("Validation (leave-one-typhoon-out P90 coverage, target ~90%)")
    from app.ml.train import leave_one_typhoon_out_p90_coverage
    for lgu, events in by_lgu.items():
        p90 = leave_one_typhoon_out_p90_coverage(events)
        if p90 is None:
            check(f"{lgu}: P90 coverage check ran", False, "not enough events to validate")
            continue
        # Judged on the LGU total and on barangays that actually received
        # packs - not the plain barangay figure, which 0-pack rows inflate.
        # FAIL = clearly broken; WARN = below the ~90% target (with 8-14
        # storms, one or two misses is normal variation - read the hits/n).
        lgu_cov, nz = p90["lgu_coverage"], p90["barangay_coverage_nonzero"]
        lgu_d = f"{lgu_cov * 100:.1f}% ({p90['lgu_hits']}/{p90['lgu_n']} storms)"
        check(f"{lgu}: municipality-level P90 coverage not broken (>= 60%)", lgu_cov >= 0.60, lgu_d)
        warn_unless(f"{lgu}: municipality-level P90 coverage near target (>= 80%)", lgu_cov >= 0.80, lgu_d)
        if nz is None:
            check(f"{lgu}: received-packs P90 coverage computed", False)
            continue
        nz_d = f"{nz * 100:.1f}% ({p90['barangay_nonzero_hits']}/{p90['barangay_nonzero_n']} barangay-storms)"
        check(f"{lgu}: P90 coverage for barangays that received packs not broken (>= 50%)", nz >= 0.50, nz_d)
        warn_unless(f"{lgu}: P90 coverage for barangays that received packs near target (>= 80%)", nz >= 0.80, nz_d)

    print("Metrics")
    m = db.session.execute(text(
        "SELECT model_version, mae, mae_baseline_equal_split, mae_baseline_avg_share "
        "FROM model_metrics ORDER BY metric_id DESC LIMIT 1")).fetchone()
    check("latest metrics row is from the current model version", m is not None and m[0] == MODEL_VERSION, str(m))

if warnings:
    print(f"\n{len(warnings)} WARNING(S) - known limits / below target, read before relying on the forecast:")
    for w in warnings:
        print(f"  - {w}")
print("\nALL CHECKS PASSED" if not failures else f"\n{len(failures)} CHECK(S) FAILED: {failures}")
sys.exit(1 if failures else 0)
