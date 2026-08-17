#!/usr/bin/env bash
# =============================================================================
# run.sh — Network Anomaly Detection: start/stop backend + open frontend dashboard
#
# Usage:
#   ./run.sh                          # start server + open browser → train from the UI
#   ./run.sh stop                     # stop a running server
#   ./run.sh --port 8080              # custom port
#   ./run.sh --no-browser             # start server only, don't open browser
#   ./run.sh --debug                  # Flask debug mode
#   ./run.sh --train                  # optional: train via CLI before serving
#   ./run.sh --train --no-plots       # CLI train without saving plots
#   ./run.sh --data path/to/data.csv  # CSV to use when training via CLI
#
# Normal workflow:
#   1. ./run.sh              → server starts, browser opens
#   2. Click "Train Pipeline" tab in the dashboard
#   3. Select data source (upload CSV or use bundled dataset)
#   4. Click "Start Training" — progress streams live to the log window
#   5. Models hot-reload automatically when training finishes
#
# This script runs Flask's own dev server (app.run()) -- fine for local use,
# but not for production. For that: `docker build -t network-anomaly-detection .`
# / `docker compose up --build` / `Procfile` (all at the project root), or see
# Reference_Guide.md §6 for the full deployment guide.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
PORT=5000
DEBUG=0
OPEN_BROWSER=1
DO_TRAIN=0
NO_PLOTS=""
DATA_ARG=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="$SCRIPT_DIR/backend/app/ml_model_pipeline/model_artifacts"
FRONTEND_URL="http://localhost:$PORT"
PID_FILE="$SCRIPT_DIR/.nad_server.pid"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERR ]${NC}  $*"; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    stop)
      STOPPED=0
      if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
          info "Stopping server (PID $PID)…"
          kill "$PID"
          STOPPED=1
        else
          warn "PID file had stale PID $PID (already dead)."
        fi
        rm -f "$PID_FILE"
      fi

      # Always sweep for any app.py Flask process too -- not just when the
      # PID file is missing. A stale/mismatched PID file (e.g. the server
      # was last started manually, bypassing run.sh, or a previous run.sh
      # instance died without cleaning up) would otherwise leave the real
      # process running and squatting on the port, with `stop` reporting
      # success and exiting having killed nothing.
      PIDS=$(pgrep -f "python.*app\.py" 2>/dev/null || true)
      if [[ -n "$PIDS" ]]; then
        echo "$PIDS" | xargs kill 2>/dev/null || true
        ok "Server process(es) stopped: $PIDS"
        STOPPED=1
      fi

      if [[ "$STOPPED" -eq 0 ]]; then
        warn "No running server found."
      else
        ok "Server stopped."
      fi
      exit 0 ;;
    --port)        PORT="$2";       FRONTEND_URL="http://localhost:$PORT"; shift 2 ;;
    --debug)       DEBUG=1;         shift ;;
    --no-browser)  OPEN_BROWSER=0;  shift ;;
    --train)       DO_TRAIN=1;      shift ;;
    --no-plots)    NO_PLOTS="--no-plots"; shift ;;
    --data)        DATA_ARG="$2";   shift 2 ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# //'
      exit 0 ;;
    *)
      error "Unknown option: $1"
      echo "  Run  ./run.sh --help  for usage."
      exit 1 ;;
  esac
done

echo ""
echo "============================================================"
echo "  Network Anomaly Detection — starting application"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Check Python
# ---------------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
  error "python3 not found. Please install Python 3.10+."
  exit 1
fi
PYTHON=$(command -v python3)
ok "Python: $($PYTHON --version)"

# ---------------------------------------------------------------------------
# Change to project root so all relative imports resolve
# ---------------------------------------------------------------------------
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Check required packages
# ---------------------------------------------------------------------------
info "Checking Python packages…"
if ! $PYTHON -c "import flask, numpy, pandas, sklearn, xgboost, joblib, matplotlib, seaborn, scipy, statsmodels" 2>/dev/null; then
  warn "Some packages are missing. Installing from requirements.txt…"
  $PYTHON -m pip install -r requirements.txt
fi
ok "All packages present"

# ---------------------------------------------------------------------------
# Optional: train first
# ---------------------------------------------------------------------------
if [[ $DO_TRAIN -eq 1 ]]; then
  info "Running training pipeline…"
  TRAIN_CMD="$PYTHON backend/app/ml_model_pipeline/train.py $NO_PLOTS"
  if [[ -n "$DATA_ARG" ]]; then
    TRAIN_CMD="$TRAIN_CMD --data $DATA_ARG"
  fi
  echo ""
  echo "  Command: $TRAIN_CMD"
  echo ""
  eval "$TRAIN_CMD"
  echo ""
  ok "Training complete"
fi

# ---------------------------------------------------------------------------
# Optional: train first (CLI / CI use only — normal use trains from the UI)
# ---------------------------------------------------------------------------
if [[ $DO_TRAIN -eq 1 ]]; then
  info "Running training pipeline…"
  TRAIN_CMD="$PYTHON backend/app/ml_model_pipeline/train.py $NO_PLOTS"
  if [[ -n "$DATA_ARG" ]]; then
    TRAIN_CMD="$TRAIN_CMD --data $DATA_ARG"
  fi
  echo ""
  echo "  Command: $TRAIN_CMD"
  echo ""
  eval "$TRAIN_CMD"
  echo ""
  ok "Training complete"
fi

# ---------------------------------------------------------------------------
# Check model artifacts — informational only, never blocks startup
# ---------------------------------------------------------------------------
PKL_COUNT=$(find "$ARTIFACTS_DIR" -maxdepth 1 -name '*.pkl' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$PKL_COUNT" -lt 9 ]]; then
  warn "No trained models found yet ($PKL_COUNT/9 artifacts)."
  warn "→ Open the dashboard and use the  Train Pipeline  tab to train from the UI."
else
  ok "$PKL_COUNT model artifacts found — ready to predict"
fi

# ---------------------------------------------------------------------------
# Start Flask server (serves backend API + frontend dashboard on same port)
# ---------------------------------------------------------------------------
export PORT="$PORT"
export FLASK_DEBUG="$DEBUG"
export MODEL_DIR="$ARTIFACTS_DIR"

info "Starting Flask server on port ${PORT}..."
info "Dashboard → ${FRONTEND_URL}"
echo ""

# Start server in background so we can open the browser after it's ready
$PYTHON app.py &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

# ---------------------------------------------------------------------------
# Trap Ctrl+C — stop the server cleanly
# ---------------------------------------------------------------------------
cleanup() {
  echo ""
  info "Shutting down server (PID $SERVER_PID)…"
  kill "$SERVER_PID" 2>/dev/null || true
  rm -f "$PID_FILE"
  ok "Server stopped."
  exit 0
}
trap cleanup SIGINT SIGTERM

# ---------------------------------------------------------------------------
# Wait for the server to be ready (max 15 s)
# ---------------------------------------------------------------------------
info "Waiting for server to be ready…"
READY=0
for i in $(seq 1 30); do
  sleep 0.5
  if curl -s "$FRONTEND_URL/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
done

if [[ $READY -eq 1 ]]; then
  ok "Server is up → $FRONTEND_URL"
else
  warn "Server did not respond within 15 s — it may still be loading models."
fi

# ---------------------------------------------------------------------------
# Open browser
# ---------------------------------------------------------------------------
if [[ $OPEN_BROWSER -eq 1 ]]; then
  info "Opening browser…"
  if command -v open &>/dev/null; then          # macOS
    open "$FRONTEND_URL"
  elif command -v xdg-open &>/dev/null; then    # Linux
    xdg-open "$FRONTEND_URL"
  elif command -v start &>/dev/null; then       # Windows (Git Bash)
    start "$FRONTEND_URL"
  else
    warn "Could not detect a browser opener. Navigate to $FRONTEND_URL manually."
  fi
fi

echo ""
echo "  Press  Ctrl+C  to stop the server."
echo ""

# ---------------------------------------------------------------------------
# Keep script alive while server runs
# ---------------------------------------------------------------------------
wait "$SERVER_PID"
