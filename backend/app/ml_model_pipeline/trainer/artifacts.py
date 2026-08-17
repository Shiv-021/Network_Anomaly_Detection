"""
backend/training/trainer/artifacts.py
========================================
Step 9 — Persist all trained artifacts to disk and build the summary dict.
"""
import os
import joblib

from .state import TrainingState


def save_artifacts(state: TrainingState) -> None:
    print("\n" + "=" * 70)
    print("SAVING ARTIFACTS → models/")
    print("=" * 70)

    def _save(obj, filename):
        path = os.path.join(state.model_dir, filename)
        joblib.dump(obj, path)
        size_kb = os.path.getsize(path) // 1024
        print(f"  Saved: {filename}  ({size_kb} KB)")

    _save(state.xgb_model,  "xgb_anomaly_model.pkl")
    _save(state.xgb_multi,  "xgb_multiclass_model.pkl")
    _save(state.le_attack,  "attack_label_encoder.pkl")
    _save(state.scaler,     "scaler.pkl")
    _save(list(state.X_train.columns), "feature_columns.pkl")
    _save(state.pca_recon,  "pca_reconstruction_model.pkl")
    _save({
        "default_threshold":            0.5,
        "recall_favoring_threshold":    float(state.chosen_threshold),
        "pca_reconstruction_threshold": state.recon_threshold,
    }, "decision_thresholds.pkl")
    _save(state.service_freq_map, "service_freq_map.pkl")
    _save(state.fallback_freq,    "fallback_freq.pkl")


def build_summary(state: TrainingState, binary_info: dict) -> dict:
    """Return the summary dict printed by train.py at the end of the pipeline."""
    return {
        "best_binary_model":     binary_info.get("best_binary_model"),
        "best_multiclass_model": state.best_multi_name,
        "chosen_threshold":      state.chosen_threshold,
        "recon_auc":             state.recon_auc,
        "n_attack_classes": (
            len(state.le_attack.classes_) if state.le_attack else None
        ),
    }
