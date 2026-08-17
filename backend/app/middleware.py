"""
backend/app/middleware.py
===========================
Request lifecycle hooks — per-request timing and access logging.

register_middleware(app) is called from factory.create_app() after the
Flask app is created and before blueprints are registered.
"""
import time
import logging
from flask import Flask, request, g

logger = logging.getLogger("anomaly-api.access")


def register_middleware(app: Flask) -> None:
    """Attach before/after request hooks to the Flask app."""

    @app.before_request
    def _start_timer() -> None:
        g.start_time = time.perf_counter()

    @app.after_request
    def _log_request(response):
        elapsed_ms = (time.perf_counter() - g.start_time) * 1000
        logger.info(
            "%s %s → %s  (%.1f ms)",
            request.method, request.path,
            response.status_code, elapsed_ms,
        )
        return response
