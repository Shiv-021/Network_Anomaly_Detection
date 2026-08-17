"""
backend/app/helpers.py
========================
Shared utilities used by multiple route handlers.

require_models(*keys) — guard that returns a 503-ready error dict when
                        any required artifact failed to load.
parse_request_records() — normalises single-record and batch request bodies
                          into a list of dicts; raises PreprocessingError
                          on bad input.
"""
import logging
from flask import request
from backend.app.ml_model_pipeline.preprocessing.preprocessor import PreprocessingError
from .services import model_service

logger = logging.getLogger("anomaly-api")


def require_models(*keys: str) -> dict | None:
    """
    Return an error dict if any required artifact is missing, else None.
    Keeps route handlers clean; call at the top of each handler.
    """
    missing = [k for k in keys if k not in model_service.artifacts]
    if missing:
        return {
            "error":   "Model artifacts not loaded.",
            "missing": missing,
            "hint":    "Use the Train Pipeline tab in the UI to train first — models reload automatically.",
        }
    return None


def parse_request_records() -> list[dict]:
    """
    Accept either:
      {"data": [{...}, ...]}   batch (preferred)
      {...}                    single record, no wrapper
    Returns a list of dicts, or raises PreprocessingError.
    """
    if not request.is_json:
        raise PreprocessingError("Request must have Content-Type: application/json.")
    body = request.get_json(silent=True)
    if body is None:
        raise PreprocessingError("Request body is not valid JSON.")
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    if isinstance(body, dict) and "records" in body:
        return body["records"]
    if isinstance(body, dict):
        return [body]
    if isinstance(body, list):
        return body
    raise PreprocessingError("Request body must be a JSON object or list of objects.")
