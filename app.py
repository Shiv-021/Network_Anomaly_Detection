"""
app.py — Network Anomaly Detection API entry point
====================================================
Thin launcher: creates the Flask app via the application factory and starts
the development server.

Usage
-----
    python app.py
    PORT=8080 python app.py
    python run.py serve           # same, via the CLI orchestrator

    # Production (this module's `app` object is the gunicorn WSGI target):
    gunicorn --config gunicorn_config.py app:app

Application logic lives in backend/app/.
See README.md for setup instructions and full API documentation, and
Reference_Guide.md for the full deployment guide (Docker, PaaS, systemd).
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
