"""
backend/training/trainer/binary_summary.py
============================================
Step 6 — Compare all binary models, save confusion matrices and ROC curves.

Writes to state:
  results_df

Returns:
  dict with 'best_binary_model' key (consumed by artifacts.build_summary).
"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_auc_score, roc_curve,
    precision_recall_fscore_support, accuracy_score,
)

from .state import TrainingState

sns.set_style("whitegrid")


def summarize_binary(state: TrainingState) -> dict:
    print("\n" + "=" * 70)
    print("MODEL COMPARISON SUMMARY (binary is_anomaly)")
    print("=" * 70)

    def get_metrics(y_true, y_pred, name, proba=None):
        p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
        auc = round(float(roc_auc_score(y_true, proba)), 4) if proba is not None else None
        row = {"Model": name,
               "Accuracy":  round(float(accuracy_score(y_true, y_pred)), 4),
               "F1":        round(float(f), 4),
               "Precision": round(float(p), 4),
               "Recall":    round(float(r), 4)}
        if auc is not None:
            row["ROC-AUC"] = auc
        return row

    rows = []
    for name, preds in state.binary_preds.items():
        proba = state.binary_probas.get(name)
        rows.append(get_metrics(state.y_test, preds, name, proba))
    # Recall-tuned variant — same probabilities as XGBoost (tuned), different threshold
    rows.append(get_metrics(state.y_test, state.y_pred_recall_tuned,
                            "XGBoost (tuned, recall-favoring threshold)",
                            state.binary_probas.get("XGBoost (tuned)")))
    state.results_df = pd.DataFrame(rows)
    print(state.results_df.to_string(index=False))

    # Confusion matrices
    n_models = len(state.binary_preds)
    n_cols   = min(n_models, 4)
    n_rows   = int(np.ceil(n_models / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 5 * n_rows))
    axes = np.array(axes).flatten()
    for ax, (name, preds) in zip(axes, state.binary_preds.items()):
        cm = confusion_matrix(state.y_test, preds)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"])
        ax.set_title(name, fontsize=9)
    for j in range(n_models, len(axes)):
        axes[j].axis("off")
    plt.tight_layout()
    state.savefig("confusion_matrices_comparison.png")

    # ROC curves
    plt.figure(figsize=(9, 7))
    for name, proba in state.binary_probas.items():
        if proba is None:
            continue
        fpr, tpr, _ = roc_curve(state.y_test, proba)
        auc = roc_auc_score(state.y_test, proba)
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves — Supervised Models")
    plt.legend(fontsize=8)
    plt.tight_layout()
    state.savefig("roc_curves.png")

    best_name = state.results_df.loc[state.results_df["F1"].idxmax(), "Model"]

    # Save comparison as JSON so the dashboard can display all models.
    # NOTE: state.results_df is built from rows with heterogeneous keys
    # (e.g. Isolation Forest rows have no "ROC-AUC" since they expose no
    # probability scores). pandas.DataFrame fills those gaps with NaN,
    # and NaN is NOT valid JSON — json.dump() happily writes a bare `NaN`
    # token, which then makes the browser's JSON.parse() throw and kills
    # the whole /model/info response (dashboard renders nothing at all).
    # Drop NaN entries instead of serializing them, same as columns that
    # were never populated for a given model.
    comp = {
        "best":   best_name,
        "models": [
            {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in row.items()
             if v is not None and not (isinstance(v, float) and np.isnan(v))}
            for row in state.results_df.to_dict(orient="records")
        ],
    }
    comp_path = os.path.join(state.model_dir, "binary_comparison.json")
    with open(comp_path, "w") as _f:
        json.dump(comp, _f, indent=2)
    print(f"  Saved: binary_comparison.json")

    return {"best_binary_model": best_name}
