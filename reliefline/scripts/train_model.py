"""
Trains the SARIMAX food-pack forecaster (app.ml.train) against the current
database and prints the rolling-origin backtest against two baselines.
Safe to re-run any time new history lands - each run adds a fresh
ModelMetrics row so accuracy over time stays visible. Afterwards sync the
dump:  bash scripts/sync_db_dump.sh

Usage:
    .venv/Scripts/python.exe scripts/train_model.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.ml.train import MODEL_VERSION, ORDER, EXOG_FEATURES, train_and_persist

app = create_app()

with app.app_context():
    out = train_and_persist()
    s = out["summary"]
    print(f"Model {MODEL_VERSION}: SARIMAX{ORDER} + {EXOG_FEATURES} per LGU {out['lgus']}")
    print(f"History used through {out['data_through']}")
    if not s:
        print("Not enough history for a backtest.")
        sys.exit(0)

    print(f"\nRolling-origin backtest: {s['folds']} fits (origins {', '.join(s['origins'])}), 12-month horizon")
    print(f"\n{'monthly accuracy':<22}{'SARIMAX':>12}{'seas-naive':>12}{'seas-mean':>12}")
    for label, key, fmt in (("MAE (packs)", "mae", "{:,.0f}"), ("RMSE (packs)", "rmse", "{:,.0f}"),
                            ("WAPE", "wape", "{:.3f}"), ("WAPE wet season", "wape_wet", "{:.3f}"),
                            ("R^2", "r2", "{:.3f}"), ("bias %", "bias_pct", "{:+.1f}")):
        print(f"{label:<22}" + "".join(f"{fmt.format(s[m][key]):>12}" for m in ("sarimax", "naive", "seasmean")))

    print(f"\n{'stock-planning error':<22}{'SARIMAX':>12}{'seas-naive':>12}{'seas-mean':>12}")
    for h in (6, 12):
        te = s["total_err"][h]
        print(f"{f'{h}-month total':<22}" + "".join(f"{te[m]:>12.3f}" for m in ("sarimax", "naive", "seasmean")))

    print(f"\nP90 safety stock coverage (target 0.90)")
    print(f"  monthly (each fit's P90 uses only its own training errors): {s['p90_month_coverage']:.2f}")
    for h, c in s["p90_total_coverage"].items():
        print(f"  {h}-month total (simulated paths, conservative if above 0.90): {c:.2f}")

    if out["holdout"]:
        print("\nReal-sample check (supply sheet, not measured need):")
        for h in out["holdout"]:
            print(f"  {h['lgu']} {h['month']}: real distributed {h['actual']:,} | "
                  f"forecast expected {h['expected']:,.0f}, P90 {h['p90']:,.0f}")
