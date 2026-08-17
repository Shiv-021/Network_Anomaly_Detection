"""
backend/app/routes/health.py
==============================
Liveness/readiness and model metadata endpoints.

GET /health           — overall API status + list of loaded artifacts
GET /model/info       — feature list, thresholds, attack classes, model comparisons
GET /api/plots        — list of available training plot files by category
GET /plots/<filename> — serve a training plot PNG file
"""
import json
import math
import os

from flask import Blueprint, jsonify, send_file

from config.columns import REQUIRED_FIELDS
from config.settings import MODEL_DIR, PLOT_DIR
from ..services import model_service
from ..helpers import require_models

bp = Blueprint("health", __name__)


def _sanitize_nan(obj):
    """Recursively replace NaN/Infinity with None.

    Python's json module (de)serializes NaN/Infinity as bare, non-standard
    tokens (`NaN`, `Infinity`). Those are NOT valid JSON — if a training
    artifact ever contains one, the browser's JSON.parse() (used by
    fetch().json() on the frontend) throws and the *entire* response is
    lost, silently breaking the training-results dashboard (metrics table
    and plots gallery both fail to render, with no visible error). Strip
    them here so a bad artifact degrades gracefully (missing cell) instead
    of taking down the whole page.
    """
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj

# All plots generated during training, organised by category
_PLOT_CATEGORIES = {
    "EDA": [
        ("class_imbalance.png",            "Class Imbalance"),
        ("attack_types.png",               "Attack Type Distribution"),
        ("numeric_distributions.png",      "Numeric Distributions"),
        ("correlation_heatmap.png",        "Correlation Heatmap"),
        ("categorical_distributions.png",  "Categorical Distributions"),
        ("rate_feature_distributions.png", "Rate Feature Distributions"),
        ("outlier_boxplots.png",           "Outlier Boxplots"),
        ("timeseries_analysis.png",        "Timeseries Analysis"),
        ("security_indicators.png",        "Security Indicators by Class"),
    ],
    "Feature Engineering": [
        ("full_distribution_grid.png",     "Full Distribution Grid"),
        ("final_correlation_heatmap.png",  "Final Correlation Heatmap"),
    ],
    "Training": [
        ("xgb_feature_importance.png",           "XGBoost Feature Importance"),
        ("threshold_tuning.png",                 "Threshold Tuning"),
        ("confusion_matrices_comparison.png",    "Confusion Matrices (All Models)"),
        ("roc_curves.png",                       "ROC Curves"),
        ("multiclass_confusion_matrix.png",      "Multiclass Confusion Matrix"),
    ],
    "Unsupervised": [
        ("pca_projection.png",             "PCA Projection (Dimensionality Reduction to 2D)"),
        ("pca_reconstruction_error.png",   "PCA Reconstruction Error (Anomaly Score via Dimensionality Reduction)"),
        ("tsne_comparison.png",            "t-SNE Comparison"),
        ("dbscan_kdistance.png",           "DBSCAN K-Distance"),
        ("dendrogram.png",                 "Hierarchical Dendrogram"),
    ],
}


@bp.route("/health")
def health():
    status = "ok" if model_service.MODELS_READY else "not_trained"
    return jsonify({
        "status":        status,
        "models_loaded": list(model_service.artifacts.keys()),
        "load_errors":   model_service.load_errors,
    }), 200


@bp.route("/model/info")
def model_info():
    err = require_models("feature_columns", "decision_thresholds")
    if err:
        return jsonify(err), 503

    info = {
        "binary_model":        "XGBoost (tuned, RandomizedSearchCV)",
        "multiclass_model":    "XGBoost (multi:softprob)",
        "feature_count":       len(model_service.artifacts["feature_columns"]),
        "raw_fields_required": REQUIRED_FIELDS,
        "decision_thresholds": model_service.artifacts["decision_thresholds"],
    }
    # "PCA Components" on the dashboard was always showing "–" because this
    # endpoint never sent a pca_components key at all (the frontend's `??
    # '–'` fallback was doing exactly what it's supposed to). Read it off
    # the actual fitted PCA model rather than hardcoding 15, so it can never
    # drift out of sync with what the trainer actually used.
    if "pca_reconstruction_model" in model_service.artifacts:
        info["pca_components"] = model_service.artifacts["pca_reconstruction_model"].n_components_
    if "attack_label_encoder" in model_service.artifacts:
        info["supported_classes"] = list(
            model_service.artifacts["attack_label_encoder"].classes_
        )

    # Include model comparison tables if they exist (saved by training pipeline)
    for key, filename in (
        ("binary_comparison",       "binary_comparison.json"),
        ("multiclass_comparison",   "multiclass_comparison.json"),
        ("unsupervised_comparison", "unsupervised_comparison.json"),
        ("cv_comparison",           "cv_comparison.json"),
    ):
        path = os.path.join(MODEL_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    info[key] = _sanitize_nan(json.load(f))
            except Exception:
                pass

    return jsonify(info)


@bp.route("/api/plots")
def list_plots():
    """Return available training plots as a flat list with category tags."""
    plots = []
    for cat, entries in _PLOT_CATEGORIES.items():
        for fname, title in entries:
            if os.path.exists(os.path.join(PLOT_DIR, fname)):
                plots.append({"filename": fname, "title": title, "category": cat})
    return jsonify({"plots": plots})


@bp.route("/plots/<filename>")
def serve_plot(filename):
    """Serve a single training plot PNG.  Path traversal is rejected."""
    # Security: only .png, no subdirectory components
    if (
        not filename.endswith(".png")
        or "/" in filename
        or "\\" in filename
        or ".." in filename
    ):
        return jsonify({"error": "Not found"}), 404
    path = os.path.join(PLOT_DIR, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "Plot not found — run training with plots enabled"}), 404
    return send_file(path, mimetype="image/png")
