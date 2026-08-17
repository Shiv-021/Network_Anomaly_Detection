#!/usr/bin/env bash
# =============================================================================
# run_container.sh — Network Anomaly Detection: build & run via container
#
# Wraps `docker compose` / `podman-compose` (whichever engine is installed)
# so you don't have to remember the exact command, flags, or which compose
# tool your engine uses. Uses the SAME Dockerfile/docker-compose.yml either
# way -- see Reference_Guide.md §6 for why no engine-specific files exist.
#
# Usage:
#   ./run_container.sh                # build + start, wait for health, open browser
#   ./run_container.sh --no-browser   # same, without opening a browser
#   ./run_container.sh stop           # stop and remove the container
#   ./run_container.sh restart        # stop, rebuild, start again
#   ./run_container.sh logs           # follow container logs (Ctrl+C to stop watching)
#   ./run_container.sh status         # show container + health status
#
# This is the containerized counterpart to run.sh (which runs Flask's dev
# server directly on the host, no container). Use this one when you want to
# run/test the app the way it'd actually run in production (gunicorn, inside
# a container) rather than for day-to-day local development.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=5000
OPEN_BROWSER=1
URL="http://localhost:${PORT}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERR ]${NC}  $*"; }

# ---------------------------------------------------------------------------
# Detect an available engine + its compose tool. Docker preferred if both are
# installed; podman-compose used as-is if that's what you have (see the
# podman-specific notes in Reference_Guide.md §6 -- no file differences
# needed, just which tool reads Dockerfile/docker-compose.yml).
# ---------------------------------------------------------------------------
ENGINE=""
COMPOSE_CMD=""

if command -v docker &>/dev/null; then
  ENGINE="docker"
  if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
  fi
fi

if [[ -z "$COMPOSE_CMD" ]] && command -v podman &>/dev/null; then
  ENGINE="podman"
  # Podman has no native macOS/Windows container runtime -- it needs a Linux
  # VM ("podman machine"). Docker Desktop manages this transparently; podman
  # doesn't, so start it here if it isn't already running.
  if podman machine list --format '{{.Name}}' &>/dev/null 2>&1; then
    if ! podman machine list --format '{{.Running}}' 2>/dev/null | grep -qi true; then
      info "Starting podman machine (Linux VM for containers)…"
      podman machine start
    fi
  fi
  if command -v podman-compose &>/dev/null; then
    COMPOSE_CMD="podman-compose"
  elif podman compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="podman compose"
  fi
fi

if [[ -z "$ENGINE" ]]; then
  error "Neither 'docker' nor 'podman' found on PATH. Install one of them first."
  exit 1
fi
if [[ -z "$COMPOSE_CMD" ]]; then
  error "$ENGINE is installed, but no compose tool was found (docker compose / docker-compose / podman-compose)."
  exit 1
fi

info "Using engine: $ENGINE   (compose: $COMPOSE_CMD)"

# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------
case "${1:-}" in
  stop|down)
    info "Stopping container…"
    $COMPOSE_CMD down
    ok "Stopped."
    exit 0 ;;
  restart)
    info "Restarting (stop, rebuild, start)…"
    $COMPOSE_CMD down || true
    shift || true
    ;;
  logs)
    info "Following logs (Ctrl+C to stop watching -- container keeps running)…"
    $COMPOSE_CMD logs -f
    exit 0 ;;
  status)
    $COMPOSE_CMD ps
    exit 0 ;;
  --no-browser)
    OPEN_BROWSER=0 ;;
esac

# ---------------------------------------------------------------------------
# Build & start (detached)
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Network Anomaly Detection — building & starting container"
echo "============================================================"
echo ""
info "This can take a few minutes on first run (installs Node + Python deps)."
$COMPOSE_CMD up -d --build

# ---------------------------------------------------------------------------
# Wait for /health (up to 2 minutes -- model artifacts can take a moment to
# load once the container's up)
# ---------------------------------------------------------------------------
info "Waiting for server to be ready…"
READY=0
for _ in $(seq 1 60); do
  sleep 2
  if curl -s "$URL/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
done

if [[ $READY -eq 1 ]]; then
  ok "Server is up → $URL"
  curl -s "$URL/health"
  echo ""
else
  warn "Server did not respond within 2 minutes — check '$COMPOSE_CMD logs -f' for details."
fi

# ---------------------------------------------------------------------------
# Open browser
# ---------------------------------------------------------------------------
if [[ $OPEN_BROWSER -eq 1 && $READY -eq 1 ]]; then
  info "Opening browser…"
  if command -v open &>/dev/null; then          # macOS
    open "$URL"
  elif command -v xdg-open &>/dev/null; then    # Linux
    xdg-open "$URL"
  fi
fi

echo ""
echo "  Container running in the background."
echo "  Stop it:      ./run_container.sh stop"
echo "  Follow logs:  ./run_container.sh logs"
echo "  Status:       ./run_container.sh status"
echo ""
