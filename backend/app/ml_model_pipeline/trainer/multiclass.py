"""
backend/training/trainer/multiclass.py
=========================================
Step 7 — Multi-class attack-type classification.

Models: Logistic Regression, Decision Tree, Random Forest, XGBoost.
Rare attack types (< 20 training samples) are grouped into 'other_rare'.

Writes to state:
  le_attack, xgb_multi, best_multi_name
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    roc_auc_score, classification_report, confusion_matrix,
)
import xgboost as xgb

from .state import TrainingState

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
RANDOM_STATE = 42


def train_multiclass(state: TrainingState) -> None:
    print("\n" + "#" * 70)
    print("# SUPERVISED MODELS — MULTI-CLASS (attack type)")
    print("#" * 70)

    MIN_COUNT = 20
    rare   = state.attack_train.value_counts()[lambda s: s < MIN_COUNT].index
    atk_tr = state.attack_train.where(~state.attack_train.isin(rare), "other_rare")
    atk_te = state.attack_test.where(~state.attack_test.isin(rare),  "other_rare")
    print(f"Grouped {len(rare)} rare attack types → 'other_rare'. "
          f"Final class count: {atk_tr.nunique()}")

    state.le_attack = LabelEncoder()
    y_tr_m = state.le_attack.fit_transform(atk_tr)
    known  = set(state.le_attack.classes_)
    atk_te_safe = atk_te.where(atk_te.isin(known), "other_rare")
    y_te_m = state.le_attack.transform(atk_te_safe)

    models_cfg = {
        "Logistic Regression": (
            LogisticRegression(max_iter=2000, random_state=RANDOM_STATE),
            state.X_train_scaled, state.X_test_scaled,
        ),
        "Decision Tree": (
            DecisionTreeClassifier(max_depth=15, min_samples_leaf=5,
                                    random_state=RANDOM_STATE),
            state.X_train, state.X_test,
        ),
        "Random Forest": (
            RandomForestClassifier(n_estimators=200, max_depth=20,
                                    random_state=RANDOM_STATE, n_jobs=-1),
            state.X_train, state.X_test,
        ),
        "XGBoost": (
            xgb.XGBClassifier(
                n_estimators=300, max_depth=8, learning_rate=0.1,
                objective="multi:softprob", eval_metric="mlogloss",
                random_state=RANDOM_STATE, n_jobs=-1,
            ),
            state.X_train, state.X_test,
        ),
    }

    multi_results = []
    preds_store   = {}
    for name, (model, X_tr, X_te) in models_cfg.items():
        model.fit(X_tr, y_tr_m)
        preds = model.predict(X_te)
        preds_store[name] = (model, preds)
        acc = accuracy_score(y_te_m, preds)
        _, _, f1_macro, _ = precision_recall_fscore_support(
            y_te_m, preds, average="macro", zero_division=0
        )
        auc_ovr = np.nan
        if hasattr(model, "predict_proba"):
            try:
                auc_ovr = roc_auc_score(
                    y_te_m, model.predict_proba(X_te),
                    multi_class="ovr", average="macro",
                )
            except Exception as exc:
                print(f"  (ROC-AUC unavailable for {name}: {exc})")
        multi_results.append({"Model": name, "Accuracy": acc,
                               "Macro F1": f1_macro, "Macro AUC (OVR)": auc_ovr})
        print(f"\n{name}: Acc={acc:.4f}  Macro F1={f1_macro:.4f}  Macro AUC={auc_ovr:.4f}")

    multi_df = pd.DataFrame(multi_results)
    print("\n--- Multi-class comparison ---")
    print(multi_df.to_string(index=False))

    state.best_multi_name = multi_df.loc[multi_df["Macro F1"].idxmax(), "Model"]

    # Save comparison JSON for dashboard display
    multi_comp = {
        "best": state.best_multi_name,
        "models": [
            {k: (round(v, 4) if isinstance(v, float) and v == v else (None if v != v else v))
             for k, v in row.items()}
            for row in multi_df.to_dict(orient="records")
        ],
    }
    multi_comp_path = os.path.join(state.model_dir, "multiclass_comparison.json")
    with open(multi_comp_path, "w") as _f:
        json.dump(multi_comp, _f, indent=2)
    print(f"  Saved: multiclass_comparison.json")

    best_model, best_preds = preds_store[state.best_multi_name]
    print(f"\nDetailed report — {state.best_multi_name}")
    print(classification_report(y_te_m, best_preds,
                                 labels=range(len(state.le_attack.classes_)),
                                 target_names=state.le_attack.classes_, zero_division=0))

    cm_m = confusion_matrix(y_te_m, best_preds)
    plt.figure(figsize=(14, 12))
    sns.heatmap(cm_m, annot=False, cmap="Blues",
                xticklabels=state.le_attack.classes_,
                yticklabels=state.le_attack.classes_)
    plt.title(f"Multi-class Confusion Matrix — {state.best_multi_name}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.xticks(rotation=90)
    plt.tight_layout()
    state.savefig("multiclass_confusion_matrix.png")

    state.xgb_multi = preds_store["XGBoost"][0]
