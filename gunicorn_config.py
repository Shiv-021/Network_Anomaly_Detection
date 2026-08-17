"""
gunicorn_config.py
====================
Production WSGI server config for the Network Anomaly Detection Flask app.
Lives at the project root, alongside app.py/run.sh, so both Docker and
Procfile-based platforms can reference it with a bare filename.

Usage (from project root, so relative imports in app.py resolve correctly):

    gunicorn --config gunicorn_config.py app:app

All values are overridable via environment variables so the same config
works unmodified across local Docker runs, Render/Railway/Heroku, etc.
"""
import os

# ---------------------------------------------------------------------------
# Bind address
# ---------------------------------------------------------------------------
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
# WORKERS DEFAULTS TO 1 -- NOT a memory-tuning choice, a correctness one.
# Training progress (backend/app/routes/training.py's `_state` dict: the log
# buffer, the SSE queue, the running subprocess handle) lives in a plain
# in-process Python dict. Each gunicorn WORKER is a separate OS process with
# its own independent copy of that dict -- with workers > 1, a
# `POST /api/train/start` handled by worker A leaves worker B with no idea
# training exists at all. If a later `GET /api/train/logs` or
# `/api/train/status` request happens to land on worker B (which it will,
# under gunicorn's normal request distribution), it reports "idle"/empty even
# though training is genuinely still running in worker A. Verified this
# exact failure mode live: /api/train/status returned "idle" while the
# container was still at ~290% CPU from an orphaned training subprocess.
# Only override this if training `_state` is refactored to live somewhere
# actually shared across processes (a file, SQLite, Redis, etc).
workers = int(os.environ.get("GUNICORN_WORKERS", 1))

# gthread (not sync) + multiple threads: with a single worker PROCESS above,
# we still want the long-lived `/api/train/logs` SSE stream (which blocks for
# the entire training run) to not stall other concurrent requests (health
# polls, plot images, predictions) -- gthread serves those on other threads
# of the same process, which also still share the same `_state` dict.
worker_class = "gthread"
threads = int(os.environ.get("GUNICORN_THREADS", 4))

# This used to default to 120s on the reasoning that "training runs in a
# background subprocess, so the request-handling timeout doesn't need to
# cover it" -- that reasoning missed that /api/train/logs's SSE connection
# IS a single request/response that stays open for the entire training run.
# Gunicorn's own worker-liveness watchdog (separate from this app's own
# [HEARTBEAT] SSE messages -- see training.py) doesn't necessarily get
# reset just by a generator yielding chunks mid-stream; confirmed live via
# `[CRITICAL] WORKER TIMEOUT (pid:N)` in the gunicorn log, firing ~2m49s
# into a RandomizedSearchCV step that runs several minutes with no print
# output, silently killing the worker serving the SSE stream and dropping
# the client's connection ("[SSE connection lost]" in the dashboard) even
# though training itself was still proceeding normally. Set well above the
# longest silent step (RandomizedSearchCV, several minutes) with headroom.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 1800))
graceful_timeout = 30
keepalive = 5

# ---------------------------------------------------------------------------
# Logging — plain to stdout/stderr; the app's own structured JSON logging
# (config/logging_config.py -> logs/nad.log) remains the source of truth for
# application-level events. Gunicorn's own logs are just access/error lines.
# ---------------------------------------------------------------------------
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
preload_app = False  # False: each worker loads models independently (simpler, avoids fork-after-load pickling edge cases with xgboost/sklearn C extensions)
max_requests = 1000       # recycle workers periodically to bound memory growth
max_requests_jitter = 100
