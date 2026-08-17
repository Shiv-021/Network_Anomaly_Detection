"""
config/settings.py
==================
Centralised project-wide paths and constants.

Import from here instead of constructing paths ad-hoc in each module:

    from config.settings import MODEL_DIR, PLOT_DIR, ARTIFACT_FILES
"""

import os

# ---------------------------------------------------------------------------
# Root paths (everything anchored to the project root, not __file__)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR           = os.path.join(PROJECT_ROOT, "logs")
MODEL_DIR         = os.path.join(PROJECT_ROOT, "backend", "app", "ml_model_pipeline", "model_artifacts")
PLOT_DIR          = os.path.join(PROJECT_ROOT, "backend", "app", "ml_model_pipeline", "plots")
TEMPLATE_DIR      = os.path.join(PROJECT_ROOT, "frontend", "templates")
FRONTEND_DIST_DIR = os.path.join(PROJECT_ROOT, "frontend", "dist")

# ---------------------------------------------------------------------------
# ML artifact registry
# ---------------------------------------------------------------------------
# Logical name → filename inside MODEL_DIR
ARTIFACT_FILES: dict[str, str] = {
    "binary_model":             "xgb_anomaly_model.pkl",
    "multiclass_model":         "xgb_multiclass_model.pkl",
    "attack_label_encoder":     "attack_label_encoder.pkl",
    "scaler":                   "scaler.pkl",
    "feature_columns":          "feature_columns.pkl",
    "pca_reconstruction_model": "pca_reconstruction_model.pkl",
    "decision_thresholds":      "decision_thresholds.pkl",
    "service_freq_map":         "service_freq_map.pkl",
    "fallback_freq":            "fallback_freq.pkl",
}

REQUIRED_ARTIFACTS: list[str] = list(ARTIFACT_FILES.values())
