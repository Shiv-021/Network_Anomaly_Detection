"""
backend/training/trainer/isolation_forest.py
===============================================
Step 5 — Isolation Forest (trained on normal-only traffic).

Two variants are evaluated:
  (a) Honest unsupervised  — contamination='auto'
  (b) Disclosed benchmark  — contamination=true anomaly rate

Writes to state:
  binary_preds["Isolation Forest (auto)"]
  binary_preds["Isolation Forest (true-rate benchmark)"]
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

from .state import TrainingState

RANDOM_STATE = 42


def train_isolation_forest(state: TrainingState) -> None:
    print("\n" + "=" * 70)
    print("Isolation Forest (trained on normal-only traffic)")
    print("=" * 70)
    X_normal = state.X_train[state.y_train == 0]

    print("\n--- (a) Honest unsupervised: contamination='auto' ---")
    iso_auto = IsolationForest(n_estimators=200, contamination="auto",
                                random_state=RANDOM_STATE, n_jobs=-1)
    iso_auto.fit(X_normal)
    y_auto = np.where(iso_auto.predict(state.X_test) == -1, 1, 0)
    print(classification_report(state.y_test, y_auto, target_names=["Normal", "Anomaly"]))
    state.binary_preds["Isolation Forest (auto)"] = y_auto

    print("\n--- (b) DISCLOSED benchmark: contamination=true anomaly rate ---")
    iso_bench = IsolationForest(n_estimators=200, contamination=state.y_train.mean(),
                                  random_state=RANDOM_STATE, n_jobs=-1)
    iso_bench.fit(X_normal)
    y_bench = np.where(iso_bench.predict(state.X_test) == -1, 1, 0)
    print(classification_report(state.y_test, y_bench, target_names=["Normal", "Anomaly"]))
    state.binary_preds["Isolation Forest (true-rate benchmark)"] = y_bench
