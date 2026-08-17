"""
backend/app/factory.py
========================
Flask application factory.

Creates the app, registers blueprints and error handlers.
Models are loaded only when artifacts are present (after training via the UI).
"""
import os
import logging
import traceback

from flask import Flask, jsonify

from config.settings import MODEL_DIR, TEMPLATE_DIR, FRONTEND_DIST_DIR
from config.logging_config import configure_logging
from .services import model_service
from .middleware import register_middleware
from .routes import dashboard, health, predictions, realtime, training

configure_logging()
logger = logging.getLogger("anomaly-api")


def create_app(model_dir: str = None) -> Flask:
    """
    Create and configure the Flask application.

    Parameters
    ----------
    model_dir : override the default MODEL_DIR (useful for tests).
    """
    _model_dir = model_dir or os.environ.get("MODEL_DIR", MODEL_DIR)

    app = Flask(__name__, template_folder=TEMPLATE_DIR)

    # Middleware (timing + access log)
    register_middleware(app)

    # Load ML artifacts only if they exist — if the model dir is empty the user
    # hasn't trained yet; the training route calls reload_models() when done.
    import glob as _glob
    import os as _os
    _has_artifacts = bool(_glob.glob(_os.path.join(_model_dir, "*.pkl")))
    if _has_artifacts:
        model_service.load_models(_model_dir)
    else:
        logger.info("model_service: no artifacts found — skipping load (train via UI first)")

    # Blueprints
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(predictions.bp)
    app.register_blueprint(realtime.bp)
    app.register_blueprint(training.bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": "Not found.",
            "available_routes": [
                "/", "/health", "/model/info",
                "/predict", "/predict/attack-type",
                "/predict/reconstruction", "/predict/full",
                "/api/stats", "/api/events",
            ],
        }), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error. Check server logs."}), 500

    logger.info("App created — model_dir=%s  models_ready=%s", _model_dir, model_service.MODELS_READY)
    return app
