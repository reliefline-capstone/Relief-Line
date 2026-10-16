"""
Trains the two-stage food-pack forecaster (app.ml.train) against the current
database and prints leave-one-typhoon-out validation for each LGU's share
model against two baselines. Safe to re-run any time new relief data lands -
each run adds a fresh ModelMetrics row. Afterwards sync the dump:
bash scripts/sync_db_dump.sh

Usage:
    .venv/Scripts/python.exe scripts/train_model.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.ml.train import MODEL_VERSION, BUFFER, train_and_persist

app = create_app()

with app.app_context():
    out = train_and_persist()
    print(f"Model {MODEL_VERSION}: two-stage (Stage 1 share regression + Stage 2 climatology/severity), "
          f"buffer {BUFFER:.0%}")
    print(f"LGUs trained: {out['lgus']}")
    print(f"Data through {out['data_through']}")
    import joblib
    from app.ml.train import ARTIFACT_PATH, SHARE_FLOOR
    art = joblib.load(ARTIFACT_PATH)
    print(f"\nStage 1 share = alpha x relief history + (1 - alpha) x family-count regression, "
          f"floor {SHARE_FLOOR:.0%} of per-family share")
    for lgu, L in art["lgu"].items():
        print(f"  {lgu:<18} alpha = {L['alpha']:.2f}   P(relief) = {L['p_relief']:.3f} relief events per calendar typhoon")

    print(f"\n{'leave-one-typhoon-out MAE (share)':<20}{'model':>10}{'equal-split':>14}{'avg-share':>12}{'folds':>8}")
    for lgu, cv in out["loto_cv"].items():
        if not cv:
            print(f"{lgu:<20}{'not enough events to validate':>44}")
            continue
        print(f"{lgu:<20}{cv['mae_model']:>10.4f}{cv['mae_equal_split']:>14.4f}"
              f"{cv['mae_avg_share']:>12.4f}{cv['n_folds']:>8}")
        beats_equal = cv["mae_model"] <= cv["mae_equal_split"]
        beats_avg = cv["mae_model"] <= cv["mae_avg_share"]
        print(f"{'':<20}{'beats equal-split: ' + str(beats_equal):<34}{'beats avg-share: ' + str(beats_avg)}")
        print(f"{'  size-weighted':<20}{cv['mae_model_weighted']:>10.4f}{cv['mae_equal_split_weighted']:>14.4f}"
              f"{cv['mae_avg_share_weighted']:>12.4f}")
        lo, hi = cv["diff_vs_pooled_weighted_ci"]
        print(f"{'  vs pooled history':<20}size-weighted {cv['mae_model_weighted']:.4f} vs "
              f"{cv['mae_pooled_history_weighted']:.4f}; model better in {cv['beats_pooled_k']} of "
              f"{cv['beats_pooled_n']} typhoons; 95% CI of difference {lo:+.4f} to {hi:+.4f}")

    print(f"\n{'leave-one-typhoon-out (packs)':<20}{'MAE':>10}{'RMSE':>10}{'n':>8}")
    for lgu, cv in out["loto_packs_cv"].items():
        if not cv:
            print(f"{lgu:<20}{'not enough events to validate':>38}")
            continue
        print(f"{lgu:<20}{cv['mae_packs']:>10.1f}{cv['rmse_packs']:>10.1f}{cv['n']:>8}")

    print(f"\n{'leave-one-typhoon-out P90 coverage (target ~90%)':<20}{'LGU-level':>14}{'barangay-level':>18}"
          f"{'received packs':>20}")
    for lgu, cv in out["loto_p90"].items():
        if not cv:
            print(f"{lgu:<20}{'not enough events to validate':>40}")
            continue
        nz = cv.get("barangay_coverage_nonzero")
        lgu_cell = f"{cv['lgu_coverage'] * 100:.1f}% ({cv['lgu_hits']}/{cv['lgu_n']})"
        nz_cell = (f"{nz * 100:.1f}% ({cv['barangay_nonzero_hits']}/{cv['barangay_nonzero_n']})"
                   if nz is not None else "n/a")
        print(f"{lgu:<20}{lgu_cell:>14}{cv['barangay_coverage'] * 100:>17.1f}%{nz_cell:>20}")

    # Defense metrics (2026-10-03) - one per claim; see app.ml.train.
    print("\nP90 stock: pinball loss (tau 0.9, packs; lower is better) + shortfall/excess, no buffer")
    print(f"{'':<16}{'level':<22}{'pinball':>10}{'ran short':>12}{'avg short':>11}{'avg excess':>12}")
    for lgu, cv in out["loto_p90"].items():
        if not cv:
            continue
        for label, pin, sh in (("municipality", cv["pinball_lgu"], cv["shortfall_lgu"]),
                               ("barangays w/ packs", cv["pinball_barangay_nonzero"],
                                cv["shortfall_barangay_nonzero"])):
            if pin is None:
                continue
            print(f"{lgu if label == 'municipality' else '':<16}{label:<22}{pin:>10,.1f}"
                  f"{str(sh['n_short']) + '/' + str(sh['n']):>12}{sh['avg_shortfall']:>11,.0f}{sh['avg_excess']:>12,.0f}")

    print("\nShare skill vs pooled history (1 - model / pooled, size-weighted; > 0 = model better)")
    for lgu, cv in out["loto_cv"].items():
        if not cv or cv.get("skill_vs_pooled") is None:
            continue
        lo, hi = cv["skill_vs_pooled_ci"]
        verdict = "tie" if lo < 0 < hi else ("model better" if lo > 0 else "pooled history better")
        print(f"  {lgu:<16}{cv['skill_vs_pooled']:+.1%}   95% interval {lo:+.1%} to {hi:+.1%}  ({verdict})")

    print("\nFloor protection (current forecast)")
    for lgu, cv in out["loto_cv"].items():
        f = (cv or {}).get("floor")
        if not f:
            continue
        print(f"  {lgu:<16}{f['n_history_below_half']} of {f['n_barangays']} barangays would get < half their "
              f"per-family share from history alone; floor lifts {f['n_floor_lifted']} "
              f"({f['share_moved_by_floor']:.1%} of the LGU's stock)")

    print(f"\nPriority ranking (held-out storms with >= 5 barangays served)")
    print(f"{'':<18}{'Spearman model':>16}{'pooled':>9}{'top-5 hit model':>18}{'pooled':>9}{'storms':>8}")
    for lgu, cv in out["loto_cv"].items():
        if not cv or not cv.get("rank_n_storms"):
            continue
        print(f"  {lgu:<16}{cv['spearman_model']:>16.2f}{cv['spearman_pooled']:>9.2f}"
              f"{cv['top_k_model']:>18.0%}{cv['top_k_pooled']:>9.0%}{cv['rank_n_storms']:>8}")

    print(f"\n{'Pack error':<20}{'MAE':>10}{'WAPE':>10}")
    for lgu, cv in out["loto_packs_cv"].items():
        if cv:
            print(f"  {lgu:<18}{cv['mae_packs']:>10.1f}{cv['wape']:>10.1%}")
