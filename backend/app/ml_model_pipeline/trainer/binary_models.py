"""
backend/training/trainer/binary_models.py
===========================================
Step 2 — Train all binary supervised classification models.

Models trained
  Logistic Regression, Decision Tree, Random Forest,
  SVM (LinearSVC + CalibratedClassifierCV), Neural Network (MLP),
  XGBoost (baseline), XGBoost (tuned via RandomizedSearchCV),
  Stacking Ensemble (LR + DT + RF → LR meta-learner)

Writes to state:
  binary_models, binary_preds, binary_probas, xgb_model
"""
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

from .state import TrainingState

warnings.filterwarnings("ignore")
RANDOM_STATE = 42


def train_binary(state: TrainingState) -> None:
    print("\n" + "#" * 70)
    print("# SUPERVISED MODELS — BINARY (is_anomaly)")
    print("#" * 70)

    def fit_eval(name, model, X_tr, y_tr, X_te, y_te):
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        proba = model.predict_proba(X_te)[:, 1] if hasattr(model, "predict_proba") else None
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        print(classification_report(y_te, preds, target_names=["Normal", "Anomaly"]))
        if proba is not None:
            print(f"ROC-AUC: {roc_auc_score(y_te, proba):.4f}")
        state.binary_models[name] = model
        state.binary_preds[name]  = preds
        state.binary_probas[name] = proba

    fit_eval(
        "Logistic Regression",
        LogisticRegression(penalty="l2", C=1.0, max_iter=1000, random_state=RANDOM_STATE),
        state.X_train_scaled, state.y_train, state.X_test_scaled, state.y_test,
    )
    fit_eval(
        "Decision Tree",
        DecisionTreeClassifier(max_depth=15, min_samples_leaf=5,
                                class_weight="balanced", random_state=RANDOM_STATE),
        state.X_train, state.y_train, state.X_test, state.y_test,
    )
    fit_eval(
        "Random Forest",
        RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=5,
                                class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
        state.X_train, state.y_train, state.X_test, state.y_test,
    )

    print("\nTraining SVM (LinearSVC) — may take a few minutes…")
    fit_eval(
        "SVM (Linear, calibrated)",
        CalibratedClassifierCV(
            LinearSVC(C=1.0, class_weight="balanced", max_iter=5000,
                      random_state=RANDOM_STATE),
            method="sigmoid", cv=3,
        ),
        state.X_train_scaled, state.y_train, state.X_test_scaled, state.y_test,
    )

    print("\nTraining Neural Network (MLP) — may take a few minutes…")
    fit_eval(
        "Neural Network (MLP)",
        MLPClassifier(
            hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
            alpha=1e-4, batch_size=256, max_iter=100, early_stopping=True,
            n_iter_no_change=10, random_state=RANDOM_STATE,
        ),
        state.X_train_scaled, state.y_train, state.X_test_scaled, state.y_test,
    )

    fit_eval(
        "XGBoost (baseline)",
        xgb.XGBClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.1,
            scale_pos_weight=state.scale_pos_weight, eval_metric="logloss",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        state.X_train, state.y_train, state.X_test, state.y_test,
    )

    print("\n" + "=" * 70)
    print("XGBoost — Hyperparameter Tuning (RandomizedSearchCV)")
    print("=" * 70)
    param_dist = {
        "n_estimators":     [150, 200, 300, 400],
        "max_depth":        [4, 6, 8, 10],
        "learning_rate":    [0.01, 0.05, 0.1, 0.2],
        "subsample":        [0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
        "min_child_weight": [1, 3, 5],
    }
    search = RandomizedSearchCV(
        xgb.XGBClassifier(scale_pos_weight=state.scale_pos_weight,
                          eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1),
        param_distributions=param_dist, n_iter=20, scoring="f1",
        cv=3, random_state=RANDOM_STATE, n_jobs=-1, verbose=1,
    )
    search.fit(state.X_train, state.y_train)
    print(f"Best params: {search.best_params_}")
    print(f"Best CV F1:  {search.best_score_:.4f}")
    state.xgb_model = search.best_estimator_
    fit_eval("XGBoost (tuned)", state.xgb_model,
             state.X_train, state.y_train, state.X_test, state.y_test)

    importance = pd.DataFrame({
        "feature":    state.X_train.columns,
        "importance": state.xgb_model.feature_importances_,
    }).sort_values("importance", ascending=False)
    print("\nTop 15 XGBoost feature importances:")
    print(importance.head(15))
    plt.figure(figsize=(10, 7))
    importance.head(20).set_index("feature")["importance"].sort_values().plot(kind="barh")
    plt.title("XGBoost (tuned) — Top 20 Feature Importances")
    plt.tight_layout()
    state.savefig("xgb_feature_importance.png")

    print("\n" + "=" * 70)
    print("Stacking Ensemble (LR + DT + RF → LR meta-learner)")
    print("=" * 70)
    fit_eval(
        "Stacking Ensemble",
        StackingClassifier(
            estimators=[
                ("logreg", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
                ("dtree",  DecisionTreeClassifier(max_depth=15, min_samples_leaf=5,
                                                  random_state=RANDOM_STATE)),
                ("rf",     RandomForestClassifier(n_estimators=100, max_depth=15,
                                                   random_state=RANDOM_STATE, n_jobs=-1)),
            ],
            final_estimator=LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
            cv=3, n_jobs=-1,
        ),
        state.X_train, state.y_train, state.X_test, state.y_test,
    )
