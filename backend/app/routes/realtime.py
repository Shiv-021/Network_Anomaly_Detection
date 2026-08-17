"""
backend/app/routes/realtime.py
================================
Real-time statistics endpoints.

GET /api/stats   — JSON snapshot of prediction counters since server start
GET /api/events  — Server-Sent Events stream; pushes a stats object every second
                   Connect with:  new EventSource('/api/events')

Production note:
  Each open /api/events connection holds one thread.  For the dev server
  (Flask's built-in Werkzeug) enable threading:
      app.run(threaded=True)
  For production use gunicorn with gevent workers:
      gunicorn -k gevent -w 1 app:app
"""
import json
import time
from flask import Blueprint, jsonify, Response, stream_with_context, request
from ..services.stats_service import stats_payload

MAX_SSE_CLIENTS = 10  # refuse new SSE connections beyond this limit
_sse_client_count = 0

bp = Blueprint("realtime", __name__)


@bp.route("/api/stats")
def api_stats():
    """Snapshot of prediction counts since server start."""
    return jsonify(stats_payload())


@bp.route("/api/events")
def api_events():
    """SSE stream — one stats JSON object per second."""
    global _sse_client_count
    if _sse_client_count >= MAX_SSE_CLIENTS:
        return jsonify({"error": "Too many SSE clients. Try again later."}), 503

    def _generate():
        global _sse_client_count
        _sse_client_count += 1
        try:
            while True:
                yield f"data: {json.dumps(stats_payload())}\n\n"
                time.sleep(1)
        except GeneratorExit:
            pass
        finally:
            _sse_client_count -= 1

    return Response(
        stream_with_context(_generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
