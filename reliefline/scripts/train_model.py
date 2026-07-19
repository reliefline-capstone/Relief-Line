"""
Trains the food-pack demand model (app.ml.train) against the current
database and prints the resulting leave-one-out cross-validation metrics.
Safe to re-run any time new allocation requests come in — each run adds a
fresh ModelMetrics row so accuracy over time stays visible.

Usage:
    .venv/Scripts/python.exe scripts/train_model.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.ml.train import train_and_persist

app = create_app()

with app.app_context():
    metrics = train_and_persist()
    n = len(metrics["predictions"])
    print(f"Trained on {n} real allocation records (leave-one-out cross-validation):")
    print(f"  MAE:  {metrics['mae']:.1f} packs")
    print(f"  RMSE: {metrics['rmse']:.1f} packs")
    print(f"  MAPE: {metrics['mape']:.1f}%")
    print(f"  R^2:  {metrics['r2']:.3f}")
    print()
    print("Actual vs. predicted (leave-one-out):")
    for actual, pred in zip(metrics["actual"], metrics["predictions"]):
        print(f"  actual={actual:.0f}\tpredicted={pred:.0f}")
