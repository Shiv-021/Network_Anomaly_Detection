"""
backend/app/__init__.py
========================
Flask application package.

Exposes create_app so callers can do:
    from backend.app import create_app
    app = create_app()
"""
import os
import sys

_HERE         = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from .factory import create_app

__all__ = ["create_app"]
