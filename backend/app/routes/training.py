"""
backend/app/routes/training.py
================================
Training pipeline management endpoints.

POST /api/upload               — upload a CSV data file
POST /api/train/use-local      — select the local Network_anomaly_data.csv
GET  /api/train/status         — current training state (idle/running/done/error)
POST /api/train/start          — start training in a background thread
GET  /api/train/logs           — SSE stream of training stdout (live + buffered)
POST /api/train/reset          — reset state back to idle
"""

import datetime
import os
import queue
import re
import subprocess
import sys
import threading

from flask import Blueprint, Response, jsonify, request, stream_with_context
from werkzeug.utils import secure_filename

from config.settings import LOG_DIR, MODEL_DIR, PROJECT_ROOT
from ..services import model_service

# Lines forwarded to the SSE stream (milestone / progress).
# Everything else is written to the log file only.
_PROGRESS_RE = re.compile(
    # Block / step / section headers
    r'^={6,}'                              # ===== separator lines
    r'|^BLOCK\s'                           # BLOCK 1, BLOCK 2 …
    r'|^STEP\s'                            # STEP 11: …
    r'|^HYPOTHESIS\s'                      # HYPOTHESIS 1: …
    r'|^OUTLIER DETECTION'
    r'|^CROSS-VALIDATION'
    r'|^DECISION THRESHOLD'
    r'|^--- '                              # --- section sub-headers ---
    r'|^######'                            # ###### SUPERVISED MODELS ######

    # Individual model training headers (exact names on their own line)
    r'|^Logistic Regression$'
    r'|^Decision Tree$'
    r'|^Random Forest$'
    r'|^SVM \('
    r'|^Neural Network'
    r'|^XGBoost'
    r'|^Stacking Ensemble'
    r'|^Isolation Forest'
    r'|Training SVM|Training Neural'       # "may take a few minutes" notices

    # Model results
    r'|ROC-AUC'
    r'|Best params:|Best CV F1:|Best by F1|Best Macro'
    r'|Recall-favoring threshold'
    r'|Acc=.*F1='                          # one-line multiclass summary
    r'|Grouped \d+ rare'
    r'|Top \d+ XGBoost'

    # Data / feature engineering progress
    r'|Shape after one-hot'
    r'|Train shape.*Test shape'
    r'|df_model shape'
    r'|Retained \d+ modeling'
    r'|Dropped '                           # dropped-feature notices
    r'|PCA explained variance'
    r'|K-Means:|DBSCAN|Hierarchical:|t-SNE'
    r'|PCA Reconstruction Error'

    # Artifact / file saves
    r'|Saved:'
    r'|Saved modeling dataset'

    # Server & completion messages
    r'|\[SERVER\]'
    r'|TRAINING COMPLETE'
    r'|Block \d+.*complete'
    r'|ARTIFACTS|PLOTS.*→'
    r'|Ready to serve|Training complete'
)
# Use word boundaries so column names like "serrorrate" / "rerrorrate" don't match
_ERROR_RE = re.compile(r'\berror\b|\bexception\b|\btraceback\b|\bfailed\b', re.IGNORECASE)

bp = Blueprint("training", __name__)

# ---------------------------------------------------------------------------
# Global training state  (single-user dev server — not thread-safe for prod)
# ---------------------------------------------------------------------------
_state: dict = {
    "status":    "idle",   # idle | running | done | error
    "log":       [],       # milestone lines (replayed for late-joining SSE clients)
    "log_queue": queue.Queue(),
    "proc":      None,
    "data_path": None,
    "data_name": None,
    "data_mb":   None,
    "log_file":  None,     # path to full verbose training log
}
_lock = threading.Lock()

UPLOAD_DIR  = os.path.join(PROJECT_ROOT, "uploads")
MAX_UPLOAD_MB = 200
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _push(line: str) -> None:
    _state["log"].append(line)
    _state["log_queue"].put(line)


# ---------------------------------------------------------------------------
# 1. Upload CSV
# ---------------------------------------------------------------------------
@bp.route("/api/upload", methods=["POST"])
def upload_data():
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only .csv files are accepted"}), 400

    fname = secure_filename(f.filename)
    path  = os.path.join(UPLOAD_DIR, fname)
    f.save(path)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        os.remove(path)
        return jsonify({"error": f"File too large ({size_mb:.1f} MB). Max {MAX_UPLOAD_MB} MB."}), 413

    _state["data_path"] = path
    _state["data_name"] = fname
    _state["data_mb"]   = round(size_mb, 1)
    return jsonify({"message": f"Uploaded {fname} ({size_mb:.1f} MB)", "name": fname, "mb": round(size_mb, 1)})


# ---------------------------------------------------------------------------
# 2. Use local data file
# ---------------------------------------------------------------------------
@bp.route("/api/train/use-local", methods=["POST"])
def use_local():
    local = os.path.join(PROJECT_ROOT, "Network_anomaly_data.csv")
    if not os.path.exists(local):
        return jsonify({"error": "Network_anomaly_data.csv not found in project root"}), 404

    size_mb = os.path.getsize(local) / (1024 * 1024)
    _state["data_path"] = local
    _state["data_name"] = "Network_anomaly_data.csv"
    _state["data_mb"]   = round(size_mb, 1)
    return jsonify({"message": f"Using local file ({size_mb:.1f} MB)", "name": "Network_anomaly_data.csv", "mb": round(size_mb, 1)})


# ---------------------------------------------------------------------------
# 3. Status
# ---------------------------------------------------------------------------
@bp.route("/api/train/status")
def train_status():
    return jsonify({
        "status":    _state["status"],
        "data_name": _state["data_name"],
        "data_mb":   _state["data_mb"],
        "log_lines": len(_state["log"]),
        "log_file":  _state["log_file"],
    })


# ---------------------------------------------------------------------------
# 4. Start training
# ---------------------------------------------------------------------------
@bp.route("/api/train/start", methods=["POST"])
def start_train():
    with _lock:
        if _state["status"] == "running":
            return jsonify({"error": "Training is already in progress"}), 409
        if not _state["data_path"] or not os.path.exists(_state["data_path"]):
            return jsonify({"error": "No data file selected. Upload a CSV or use local data first."}), 400

        body      = request.get_json(silent=True) or {}
        no_plots  = bool(body.get("no_plots", False))

        # Reset log
        _state["status"] = "running"
        _state["log"]    = []
        while not _state["log_queue"].empty():
            try:
                _state["log_queue"].get_nowait()
            except queue.Empty:
                break

        cmd = [
            sys.executable, "-u",
            os.path.join(PROJECT_ROOT, "backend", "app", "ml_model_pipeline", "train.py"),
            "--data", _state["data_path"],
        ]
        if no_plots:
            cmd.append("--no-plots")

        def _run():
            os.makedirs(LOG_DIR, exist_ok=True)
            ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(LOG_DIR, f"training_{ts}.log")
            _state["log_file"] = log_path
            in_summary = False   # True once we reach the TRAINING COMPLETE block

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=PROJECT_ROOT,
                    text=True,
                    bufsize=1,
                )
                _state["proc"] = proc
                with open(log_path, "w", encoding="utf-8") as lf:
                    for raw_line in proc.stdout:
                        line = raw_line.rstrip("\n")
                        # Full verbose output always written to file
                        lf.write(raw_line)
                        lf.flush()
                        # Once we hit the summary block, forward everything
                        if "TRAINING COMPLETE" in line:
                            in_summary = True
                        # SSE: only milestone lines (or errors)
                        if in_summary or _PROGRESS_RE.search(line) or _ERROR_RE.search(line):
                            _push(line)
                proc.wait()
                if proc.returncode == 0:
                    # Reload models BEFORE sending the done sentinel so the
                    # frontend's /model/info fetch always sees fresh artifacts
                    try:
                        model_service.reload_models(MODEL_DIR)
                        _push("[SERVER] Models hot-reloaded successfully.")
                    except Exception as exc:
                        _push(f"[SERVER][WARN] Model reload failed: {exc}")
                    _state["status"] = "done"
                else:
                    _state["status"] = "error"
                    _push(f"[SERVER] Training exited with code {proc.returncode}")
                # Sentinel so SSE clients know we're done
                _state["log_queue"].put(None)
            except Exception as exc:
                _push(f"[SERVER][ERROR] {exc}")
                _state["log_queue"].put(None)
                _state["status"] = "error"

        threading.Thread(target=_run, daemon=True, name="trainer").start()

    return jsonify({"message": "Training started"})


# ---------------------------------------------------------------------------
# 5. SSE log stream
# ---------------------------------------------------------------------------
@bp.route("/api/train/logs")
def train_logs():
    """
    Server-Sent Events stream of training stdout.
    Replays the full buffered log first, then streams live output.
    """
    def generate():
        # Replay history for late-joining clients
        for line in list(_state["log"]):
            yield f"data: {line}\n\n"

        # If already finished, send status and close
        if _state["status"] in ("done", "error", "idle"):
            yield f"data: [STATUS:{_state['status']}]\n\n"
            return

        # Stream live
        while True:
            try:
                line = _state["log_queue"].get(timeout=30)
            except queue.Empty:
                yield "data: [HEARTBEAT]\n\n"
                continue
            if line is None:          # sentinel — training subprocess finished
                yield f"data: [STATUS:{_state['status']}]\n\n"
                break
            yield f"data: {line}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# 6. Reset
# ---------------------------------------------------------------------------
@bp.route("/api/train/reset", methods=["POST"])
def reset_train():
    with _lock:
        if _state["status"] == "running":
            return jsonify({"error": "Cannot reset while training is running"}), 409
        _state["status"]    = "idle"
        _state["log"]       = []
        _state["data_path"] = None
        _state["data_name"] = None
        _state["data_mb"]   = None
        _state["log_file"]  = None
    return jsonify({"message": "Reset"})
