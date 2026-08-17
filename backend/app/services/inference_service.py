"""
backend/app/services/inference_service.py
==========================================
ML inference business logic — wraps raw model calls into clean result dicts.

All inference routes in backend/app/routes/predictions.py delegate here so
that the HTTP layer stays thin and the ML logic is independently testable.

Public API
----------
    run_binary(records, threshold)  → list[BinaryResult]
    run_multiclass(records)         → list[MulticlassResult]
    run_reconstruction(records)     → list[ReconResult]
    run_full(records)               → list[FullResult]

    Each function raises :class:`InferenceError` on failure.
"""
import logging
from typing import Any

import numpy as np

from backend.app.ml_model_pipeline.preprocessing.preprocessor import (
    preprocess,
    PreprocessingError,
)
from .model_service import artifacts

logger = logging.getLogger("anomaly-api")


class InferenceError(Exception):
    """Raised when inference cannot proceed (missing model, bad input, etc.)."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require(*keys: str) -> None:
    """Raise InferenceError(503) if any artifact key is absent."""
    missing = [k for k in keys if k not in artifacts]
    if missing:
        raise InferenceError(
            f"Model artifacts not loaded: {missing}. "
            "Use the Train Pipeline tab in the UI to train first.",
            status_code=503,
        )


def _preprocess(records: list[dict]) -> Any:
    """Preprocess records; raises InferenceError on bad input."""
    try:
        return preprocess(records, artifacts)
    except PreprocessingError as e:
        raise InferenceError(str(e), status_code=400) from e
    except Exception as e:
        logger.exception("Unexpected preprocessing error")
        raise InferenceError("Failed to process request payload.", status_code=400) from e


def _default_binary_threshold() -> float:
    return artifacts.get("decision_thresholds", {}).get("default_threshold", 0.5)


# ---------------------------------------------------------------------------
# Public inference functions
# ---------------------------------------------------------------------------

def run_binary(records: list[dict], threshold: float | None = None) -> list[dict]:
    """Binary is-anomaly prediction using the tuned XGBoost model.

    Returns: [{ is_anomaly, anomaly_probability, threshold_used }, ...]
    """
    _require("binary_model", "feature_columns", "service_freq_map", "fallback_freq", "decision_thresholds")
    X = _preprocess(records)
    thr = threshold if threshold is not None else _default_binary_threshold()
    try:
        proba = artifacts["binary_model"].predict_proba(X)[:, 1]
    except Exception as e:
        logger.exception("Binary model inference failed")
        raise InferenceError("Binary model inference failed.") from e

    return [
        {
            "is_anomaly":          bool(p >= thr),
            "anomaly_probability": float(p),
            "threshold_used":      thr,
        }
        for p in proba
    ]


def run_multiclass(records: list[dict]) -> list[dict]:
    """Multi-class attack-type prediction.

    Returns: [{ predicted_class, confidence, class_probabilities }, ...]
    """
    _require("multiclass_model", "attack_label_encoder", "feature_columns",
             "service_freq_map", "fallback_freq")
    X = _preprocess(records)
    try:
        proba   = artifacts["multiclass_model"].predict_proba(X)
        indices = np.argmax(proba, axis=1)
        classes = artifacts["attack_label_encoder"].classes_
    except Exception as e:
        logger.exception("Multiclass model inference failed")
        raise InferenceError("Multiclass model inference failed.") from e

    return [
        {
            "predicted_class":    classes[idx],
            "confidence":         float(proba[i, idx]),
            "class_probabilities": {
                cls: float(proba[i, j]) for j, cls in enumerate(classes)
            },
        }
        for i, idx in enumerate(indices)
    ]


def run_reconstruction(records: list[dict]) -> list[dict]:
    """Unsupervised anomaly score via PCA reconstruction error.

    Returns: [{ reconstruction_error, is_anomaly, threshold_used }, ...]
    """
    _require("pca_reconstruction_model", "scaler", "feature_columns",
             "service_freq_map", "fallback_freq", "decision_thresholds")
    X = _preprocess(records)
    thresholds = artifacts["decision_thresholds"]
    # Key written by the trainer is "pca_reconstruction_threshold" (see
    # trainer/artifacts.py) — this used to read "pca_threshold", a key that
    # never existed, so recon_thr was always None and every reconstruction
    # response silently returned is_anomaly=null / threshold_used=null.
    recon_thr  = thresholds.get("pca_reconstruction_threshold")
    try:
        # The PCA reconstruction model was FIT ON SCALED data during
        # training (trainer/dimensionality_reduction.py does
        # scaler.transform(...) before PCA.fit(...)/PCA.transform(...)).
        # _preprocess() only returns the raw, unscaled feature matrix
        # (that's all XGBoost needs, since tree models are scale-invariant)
        # — feeding that raw matrix straight into the PCA model made every
        # request come back with an astronomically large, meaningless
        # reconstruction error (millions vs. a training threshold of
        # ~0.45), so effectively everything was flagged anomalous. Scale
        # with the same fitted StandardScaler used at training time first.
        X_scaled    = artifacts["scaler"].transform(X)
        pca         = artifacts["pca_reconstruction_model"]
        X_recon     = pca.inverse_transform(pca.transform(X_scaled))
        errors      = np.mean((X_scaled - X_recon) ** 2, axis=1)
    except Exception as e:
        logger.exception("PCA reconstruction inference failed")
        raise InferenceError("PCA reconstruction inference failed.") from e

    return [
        {
            "reconstruction_error": float(err),
            "is_anomaly":           bool(err >= recon_thr) if recon_thr is not None else None,
            "threshold_used":       recon_thr,
        }
        for err in errors
    ]


def run_full(records: list[dict]) -> list[dict]:
    """Run binary + multiclass + PCA reconstruction in one call.

    Returns: [{ binary: {...}, attack_type: {...}, reconstruction: {...} }, ...]
    """
    _require(
        "binary_model", "multiclass_model", "attack_label_encoder",
        "pca_reconstruction_model", "scaler", "feature_columns",
        "service_freq_map", "fallback_freq", "decision_thresholds",
    )
    binary  = run_binary(records)
    multi   = run_multiclass(records)
    recon   = run_reconstruction(records)

    return [
        {
            "binary":         b,
            "attack_type":    m,
            "reconstruction": r,
        }
        for b, m, r in zip(binary, multi, recon)
    ]
