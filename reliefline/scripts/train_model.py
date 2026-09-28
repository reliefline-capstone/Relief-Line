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

    print(f"\n{'leave-one-typhoon-out (packs)':<20}{'MAE':>10}{'RMSE':>10}{'n':>8}")
    for lgu, cv in out["loto_packs_cv"].items():
        if not cv:
            print(f"{lgu:<20}{'not enough events to validate':>38}")
            continue
        print(f"{lgu:<20}{cv['mae_packs']:>10.1f}{cv['rmse_packs']:>10.1f}{cv['n']:>8}")
