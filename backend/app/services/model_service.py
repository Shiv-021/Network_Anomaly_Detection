"""
backend/app/services/model_service.py
========================================
ML artifact loader — loads all .pkl files once at app startup and exposes
them to the rest of the application.

Public API
----------
    load_models(model_dir)  — called by factory.create_app()
    reload_models(model_dir) — hot-reload after training completes
    artifacts               — dict[str, Any]  populated on load
    load_errors             — dict[str, str]  non-empty on partial failure
    MODELS_READY            — True only when all required artifacts loaded
"""
import os
import logging

import joblib

from config.settings import ARTIFACT_FILES

logger = logging.getLogger("anomaly-api")

# Module-level state (singleton pattern — one model set per process)
artifacts: dict    = {}
load_errors: dict  = {}
MODELS_READY: bool = False


def load_models(model_dir: str) -> None:
    """Load every artifact listed in ARTIFACT_FILES from *model_dir*.

    Clears any previously loaded artifacts before loading.
    Called once by :func:`backend.app.factory.create_app`.
    """
    global MODELS_READY
    artifacts.clear()
    load_errors.clear()

    for key, filename in ARTIFACT_FILES.items():
        path = os.path.join(model_dir, filename)
        try:
            artifacts[key] = joblib.load(path)
            logger.info("Loaded %s  (%s)", key, path)
        except FileNotFoundError:
            load_errors[key] = f"file not found at {path}"
            logger.warning("Could not load %s — file not found at %s", key, path)
        except Exception as exc:  # noqa: BLE001
            load_errors[key] = str(exc)
            logger.warning("Could not load %s: %s", key, exc)

    MODELS_READY = len(load_errors) == 0
    logger.info(
        "model_service: loaded=%d  errors=%d  ready=%s",
        len(artifacts), len(load_errors), MODELS_READY,
    )


def reload_models(model_dir: str) -> None:
    """Hot-reload artifacts after a training run completes.

    Identical to :func:`load_models` — kept as a separate name so call
    sites in the training route can signal intent clearly.
    """
    logger.info("model_service: hot-reloading artifacts from %s", model_dir)
    load_models(model_dir)
