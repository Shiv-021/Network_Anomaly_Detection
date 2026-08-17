"""
backend/training/trainer/cross_validation.py
==============================================
Step 3 — Stratified 5-fold cross-validation for the four fast models.
"""
import json
import os
import warnings

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

from .state import TrainingState

warnings.filterwarnings("ignore")
RANDOM_STATE = 42


def run_cross_validation(state: TrainingState) -> None:
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION — Stratified 5-Fold (fast models only)")
    print("=" * 70)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    targets = {
        "Logistic Regression": (
            LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
            state.X_train_scaled,
        ),
        "Decision Tree": (
            DecisionTreeClassifier(max_depth=15, min_samples_leaf=5,
                                    random_state=RANDOM_STATE),
            state.X_train,
        ),
        "Random Forest": (
            RandomForestClassifier(n_estimators=200, max_depth=20,
                                    random_state=RANDOM_STATE, n_jobs=-1),
            state.X_train,
        ),
        "XGBoost (tuned)": (state.xgb_model, state.X_train),
    }
    cv_rows = []
    for name, (est, X_data) in targets.items():
        f1  = cross_val_score(est, X_data, state.y_train, cv=skf,
                              scoring="f1",      n_jobs=-1)
        auc = cross_val_score(est, X_data, state.y_train, cv=skf,
                              scoring="roc_auc", n_jobs=-1)
        print(f"{name}: F1={f1.mean():.4f}±{f1.std():.4f}  "
              f"AUC={auc.mean():.4f}±{auc.std():.4f}")
        cv_rows.append({
            "Model":     name,
            "CV F1":     round(float(f1.mean()), 4),
            "F1 Std":    round(float(f1.std()),  4),
            "CV ROC-AUC": round(float(auc.mean()), 4),
            "AUC Std":   round(float(auc.std()),  4),
        })

    best_cv = max(cv_rows, key=lambda r: r["CV F1"])["Model"]
    cv_comp = {"best": best_cv, "models": cv_rows}
    cv_path = os.path.join(state.model_dir, "cv_comparison.json")
    with open(cv_path, "w") as _f:
        json.dump(cv_comp, _f, indent=2)
    print(f"  Saved: cv_comparison.json")
