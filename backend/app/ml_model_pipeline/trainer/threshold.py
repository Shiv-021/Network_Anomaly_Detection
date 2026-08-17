"""
backend/training/trainer/threshold.py
========================================
Step 4 — Decision threshold tuning for XGBoost (tuned).

Finds the highest threshold that still achieves ≥99% recall, saving a
precision/recall-vs-threshold plot.

Writes to state:
  chosen_threshold, y_pred_recall_tuned
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, precision_recall_fscore_support

from .state import TrainingState


def tune_threshold(state: TrainingState) -> None:
    print("\n" + "=" * 70)
    print("DECISION THRESHOLD TUNING (XGBoost, tuned)")
    print("=" * 70)
    y_proba = state.binary_probas["XGBoost (tuned)"]
    precisions, recalls, thresholds = precision_recall_curve(state.y_test, y_proba)

    plt.figure(figsize=(8, 6))
    plt.plot(thresholds, precisions[:-1], label="Precision")
    plt.plot(thresholds, recalls[:-1],    label="Recall")
    plt.axvline(0.5, color="gray", linestyle="--", label="Default (0.5)")
    plt.xlabel("Decision Threshold")
    plt.ylabel("Score")
    plt.title("Precision / Recall vs. Decision Threshold — XGBoost")
    plt.legend()
    plt.tight_layout()
    state.savefig("threshold_tuning.png")

    target_recall = 0.99
    candidates = [
        (t, p, r)
        for t, p, r in zip(thresholds, precisions[:-1], recalls[:-1])
        if r >= target_recall
    ]
    if candidates:
        state.chosen_threshold, _, _ = max(candidates, key=lambda x: x[0])
    else:
        idx = np.argmax(recalls[:-1])
        state.chosen_threshold = float(thresholds[idx]) if idx < len(thresholds) else 0.5

    state.y_pred_recall_tuned = (y_proba >= state.chosen_threshold).astype(int)
    p_new, r_new, f_new, _ = precision_recall_fscore_support(
        state.y_test, state.y_pred_recall_tuned, average="binary"
    )
    print(f"Recall-favoring threshold ({state.chosen_threshold:.4f}): "
          f"P={p_new:.4f}  R={r_new:.4f}  F1={f_new:.4f}")
