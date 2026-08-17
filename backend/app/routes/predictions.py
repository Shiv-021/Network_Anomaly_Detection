"""
backend/app/routes/predictions.py
====================================
All inference endpoints — thin HTTP wrappers that delegate to
backend.app.services.inference_service.

POST /predict                  Binary is_anomaly (XGBoost tuned)
POST /predict/attack-type      Multi-class attack type (XGBoost)
POST /predict/reconstruction   Unsupervised PCA reconstruction error
POST /predict/full             All three in one request
"""
from flask import Blueprint, request, jsonify

from ..helpers import parse_request_records
from ..services import inference_service, stats_service, model_service
from ..services.inference_service import InferenceError

bp = Blueprint("predictions", __name__)


@bp.route("/predict", methods=["POST"])
def predict_binary():
    """Binary is_anomaly prediction using the tuned XGBoost model."""
    try:
        records   = parse_request_records()
        threshold = request.args.get("threshold", type=float)
        results   = inference_service.run_binary(records, threshold)
    except InferenceError as e:
        return jsonify({"error": str(e)}), e.status_code

    for r in results:
        stats_service.record_prediction(r["is_anomaly"])
    return jsonify({"predictions": results, "count": len(results)})


@bp.route("/predict/attack-type", methods=["POST"])
def predict_multiclass():
    """Multi-class attack-type prediction (includes 'normal' and 'other_rare')."""
    try:
        records = parse_request_records()
        results = inference_service.run_multiclass(records)
    except InferenceError as e:
        return jsonify({"error": str(e)}), e.status_code
    return jsonify({"predictions": results, "count": len(results)})


@bp.route("/predict/reconstruction", methods=["POST"])
def predict_reconstruction():
    """Unsupervised anomaly score via PCA reconstruction error."""
    try:
        records = parse_request_records()
        results = inference_service.run_reconstruction(records)
    except InferenceError as e:
        return jsonify({"error": str(e)}), e.status_code

    for r in results:
        if r["is_anomaly"] is not None:
            stats_service.record_prediction(r["is_anomaly"])
    return jsonify({"predictions": results, "count": len(results)})


@bp.route("/predict/full", methods=["POST"])
def predict_full():
    """Binary + multi-class + PCA reconstruction in a single request."""
    try:
        records = parse_request_records()
        results = inference_service.run_full(records)
    except InferenceError as e:
        return jsonify({"error": str(e), "load_errors": model_service.load_errors}), e.status_code

    for item in results:
        if "binary" in item:
            stats_service.record_prediction(item["binary"]["is_anomaly"])
    return jsonify({"predictions": results, "count": len(results)})
