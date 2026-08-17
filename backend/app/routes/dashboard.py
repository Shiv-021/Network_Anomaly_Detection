"""
backend/app/routes/dashboard.py
=================================
GET /        — Serve the React app (frontend/dist/index.html).
GET /assets/ — Serve Vite build assets.
"""
import os
from flask import Blueprint, send_from_directory
from config.settings import FRONTEND_DIST_DIR

bp = Blueprint("dashboard", __name__)

_REACT_INDEX = os.path.join(FRONTEND_DIST_DIR, "index.html")


@bp.route("/")
def index():
    if os.path.isfile(_REACT_INDEX):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    return ("React build not found. Run: cd frontend && npm run build", 503)


@bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve Vite's hashed JS/CSS bundles from frontend/dist/assets/."""
    assets_dir = os.path.join(FRONTEND_DIST_DIR, "assets")
    # Prevent path traversal
    safe = os.path.realpath(os.path.join(assets_dir, filename))
    if not safe.startswith(os.path.realpath(assets_dir)):
        from flask import abort
        abort(403)
    return send_from_directory(assets_dir, filename)
