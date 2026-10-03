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
