# =============================================================================
# Dockerfile — Network Anomaly Detection
#
# Multi-stage build: compile the React/Vite dashboard, then package it with
# the Flask API + trained model artifacts into a single production image
# served by gunicorn.
#
# Lives at the project root alongside app.py/run.sh so it works with plain,
# unqualified Docker commands — no -f flag or special build context needed:
#
#   docker build -t network-anomaly-detection .
#   docker run -p 5000:5000 network-anomaly-detection
#
# Or via docker-compose.yml (same folder):
#
#   docker compose up --build
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — build the React dashboard
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — Python runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime
WORKDIR /app

# build-essential is required to compile a couple of scientific-python wheels
# (e.g. xgboost/scipy) on some platforms; safe to keep even where a prebuilt
# wheel is used.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# xgboost's Linux wheel pulls in nvidia-nccl-cu12 (~340 MB) as a hard pip
# dependency even for pure CPU use -- it's xgboost's optional multi-GPU
# distributed-training backend, unused by this single-node CPU service.
# Verified (see Reference_Guide.md §6) that fit()/predict()/predict_proba()
# all work identically with it removed. Must uninstall in the SAME RUN layer
# as the install, not a later one -- OCI layers are immutable, so removing it
# in a separate step would leave the ~340 MB in an earlier layer and not
# actually shrink the image.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y nvidia-nccl-cu12

# App code, config, training pipeline, and (if already trained) the 9 model
# artifacts under backend/app/ml_model_pipeline/model_artifacts/ — the image
# is ready to serve predictions immediately if artifacts already exist in the
# build context; otherwise it starts in "not trained" mode and the dashboard's
# Train Pipeline tab (or `python run.py train`) can be used post-deploy.
COPY . .

# Overwrite the placeholder frontend/dist with the real build from stage 1.
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PORT=5000 \
    FLASK_DEBUG=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Basic container-level health check against the Flask /health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,os,sys; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",5000)}/health', timeout=3).read()" || exit 1

CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
