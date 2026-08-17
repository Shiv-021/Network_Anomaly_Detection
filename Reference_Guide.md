# Network Anomaly Detection — Reference Guide

A complete data-science case study on top of this project: EDA + hypothesis testing → feature engineering
→ supervised & unsupervised modeling → live Flask/React deployment. See the main [`README.md`](README.md)
for the same case-study narrative in condensed form; this document is the deeper technical reference —
extended methodology detail and the full deployment guide (Podman specifics, Render/Railway/Heroku,
bare-metal `systemd`).

**Related deliverables in this repo**

| Path | Contents |
|---|---|
| [`notebooks/Network_Anomaly_Detection_Standalone.ipynb`](notebooks/Network_Anomaly_Detection_Standalone.ipynb) | Fully self-contained notebook — the same pipeline logic inlined directly in its own cells, not a reimplementation. Running it top-to-bottom reproduces the actual production pipeline's behavior, with no dependency on the `backend` package |
| [`Dockerfile`](Dockerfile), [`docker-compose.yml`](docker-compose.yml), [`gunicorn_config.py`](gunicorn_config.py), [`Procfile`](Procfile) | Deployment layer, integrated directly at the project root alongside `app.py`/`run.sh` (see §6) |
| [`run_container.sh`](run_container.sh) | One-command build/start/stop wrapper — auto-detects Docker or Podman |

**Two ways to run this pipeline:** the real production code path — `python run.py train` (CLI) or the
dashboard's Train Pipeline tab — which runs `backend/app/ml_model_pipeline/train.py` directly; or the
notebook above, which reproduces the exact same logic inlined in its own cells for a narrated,
step-by-step walkthrough. Both produce the same models and metrics.

---

## 1. Problem Statement

Network intrusion — compromised devices, malware, DDoS, brute-force logins, port scans — has to be caught
inside continuous, noisy, high-volume network traffic, and traditional signature/rule-based detection
can't keep up with attack patterns that don't match a known signature and doesn't scale as networks grow
in complexity.

**Goal:** given a single network connection's raw features (protocol, service, byte counts, error rates,
login/host statistics, etc.), determine in real time:

1. **Is this connection anomalous?** (binary detection)
2. **If so, what type of attack is it?** (multi-class classification — DoS, Probe, R2L, U2R, or a specific
   named attack)
3. Provide an **independent, label-free safety net** capable of flagging attack patterns the labeled
   models above have never seen (unsupervised anomaly detection)

**Dataset:** [NSL-KDD](Network_anomaly_data.csv) — 125,973 connection records, 41 raw features (reduced
from the classic KDD Cup 1999 dataset specifically to remove ~78% duplicate records and rebalance class
distribution), spanning **23 distinct attack types** across four broad attack categories (DoS, Probe, R2L,
U2R) plus normal traffic.

## 2. Target Metric

| Task | Primary metric | Why |
|---|---|---|
| Binary detection (`is_anomaly`) | **F1‑score**, with **Recall** prioritized via threshold tuning | A security tool's cost of a missed attack (false negative) is asymmetrically higher than a false alarm; F1 balances precision/recall while threshold tuning explicitly favors recall |
| Multi-class attack type | **Macro F1** | Treats every attack class equally regardless of frequency, so the model isn't rewarded for only doing well on the most common attack types |
| Unsupervised methods | **ROC-AUC** (PCA reconstruction error) / **Silhouette + Davies-Bouldin** (clustering) | No labels used at training time, so evaluation has to either compare the anomaly *score* against the held-out label (ROC-AUC) or measure cluster quality on its own terms |

Secondary metrics (Accuracy, Precision, Recall individually, ROC-AUC per model) are all reported in full in
§4 for transparency, since optimizing for a single number can hide operationally important trade-offs
(e.g. a model with slightly lower F1 but perfect precision may be preferable when false alarms are
expensive to triage).

---

## 3. Methodology

Full detail, code, and plots: **[`notebooks/Network_Anomaly_Detection_Standalone.ipynb`](notebooks/Network_Anomaly_Detection_Standalone.ipynb)** —
every step function (`analyze_target`, `train_binary`, etc.) reproduces the exact logic of the
corresponding `backend/app/ml_model_pipeline/` step, the same code the dashboard's Train Pipeline tab
runs, inlined directly rather than imported. Summary:

### 3.1 Exploratory Data Analysis (11 steps)

1. **Target construction** — binary `is_anomaly` from the 23-way `attack` label; class balance check (see
   §4).
2. **Known artifact check** — `lastflag` identified and excluded as a KDD-Cup difficulty-score metadata
   field, not a real network feature (would otherwise leak the answer).
3. **Numeric distributions** — `duration`, `srcbytes`, `dstbytes`, `count`, `srvcount` are heavily
   right-skewed; log1p transforms added.
4. **Hypothesis testing** (§3.2 below).
5. **Correlation analysis** — full pre-engineering Pearson correlation heatmap.
6. **Data quality** — missing values and duplicate rows checked (0 of each found — a known property of
   the pre-cleaned NSL-KDD release).
7. **Categorical distributions** — `protocoltype`, `service`, `flag`.
8. **Rate-feature distributions** — 8 `*rate` columns.
9. **Outlier detection** — Tukey 1.5×IQR fences on the 5 core numeric columns.
10. **Temporal structure** — no real timestamp exists; row-order used as a weak proxy (Kendall's Tau
    trend test, lag-1 autocorrelation) — informs the decision to use a **stratified random**, not
    chronological, train/test split.
11. **Security-indicator comparison** — 9 content/host features (failed logins, root shell, compromised
    counts, …) compared Normal vs. Anomaly by % non-zero and mean value.

### 3.2 Hypothesis Testing

| # | Hypothesis | Test | Result |
|---|---|---|---|
| H1 | `srcbytes`/`dstbytes` differ between normal and anomalous connections | Welch's t-test | **p = 0.0498** (srcbytes) — borderline significant |
| H2 | `protocoltype` distribution differs by class | χ² test of independence | **p ≈ 0.0000** — highly significant |
| H3 | `service` is associated with anomalies | χ² test of independence | **p ≈ 0.0000** — highly significant |
| H4 | `flag` (connection status) is associated with anomalies | χ² test + logistic regression | **p ≈ 0.0000** — highly significant |
| H5 | Urgent packets increase anomaly likelihood | Descriptive means + logistic regression coefficient | Directionally positive; **no formal p-value computed** in the current pipeline (flagged as a gap — see §6) |

**Takeaway:** categorical connection metadata (protocol/service/flag) is a dramatically stronger signal
than raw byte counts — this directly foreshadows why tree-based models dominate in §4.1.

### 3.3 Feature Engineering (6 steps)

1. **New features:** `is_s0_flag` (SYN-only scan indicator), `is_icmp`, `is_zero_byte_conn` — all three
   kept, all three correlate meaningfully with `is_anomaly` at zero added multicollinearity cost.
2. **Distribution diagnostics** on the expanded feature set.
3. **Redundant-feature removal:** `total_error_rate` (linear combination of two already-kept columns),
   `bytes_ratio` (**VIF ≈ 415**, correlation with target ≈ 0.006 — high collinearity cost for ~zero
   signal), `numoutboundcmds` (zero variance — constant in this dataset).
4. **VIF check** across 18 numeric/engineered candidates — conventional "> ~10 is concerning" guideline
   applied as a diagnostic (currently print-only, not yet an automated drop — see §6).
5. **Final correlation heatmap** (post-engineering).
6. **Feature selection** — final modeling set: **43 features** (3 categorical + 37 numeric + 3 engineered)
   + 2 targets (`is_anomaly`, `attack`).

### 3.4 Modeling

- **Encoding:** one-hot (`protocoltype`, `flag`, `drop_first=True`) + frequency encoding (`service`, with
  a lowest-observed-frequency fallback for unseen services at inference).
- **Split:** stratified 80/20 (100,778 train / 25,195 test) — informed by §3.1 step 10.
- **Binary classifiers:** Logistic Regression, Decision Tree, Random Forest, SVM (LinearSVC, calibrated),
  Neural Network (MLP), XGBoost (baseline), XGBoost (tuned via `RandomizedSearchCV`, 20 iterations),
  Stacking Ensemble (LR+DT+RF → LR meta-learner), Isolation Forest (honest `contamination='auto'` +
  disclosed true-rate benchmark).
- **Decision threshold tuning:** scans the tuned XGBoost's precision/recall curve for the highest
  threshold that still holds ≥99% recall.
- **Cross-validation:** stratified 5-fold on the 4 fastest models, to confirm the held-out test-set scores
  aren't a lucky split.
- **Multi-class:** the 10 rarest of 23 attack types grouped into `other_rare` (14 final classes);
  Logistic Regression, Decision Tree, Random Forest, XGBoost.
- **Unsupervised:** K-Means, DBSCAN (auto `eps` via k-distance plot), Hierarchical/Agglomerative
  clustering — plus, kept in a **separate module** since it's a different technique from clustering,
  dimensionality reduction: PCA 2D projection (visualization), t-SNE (visualization), and **PCA
  Reconstruction Error** (an actual servable, label-free anomaly detector).

---

## 4. Final Results

### 4.1 Binary classification (`is_anomaly`) — held-out test set, 25,195 rows

| Model | Accuracy | F1 | Precision | Recall | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.9554 | 0.9517 | 0.9599 | 0.9436 | 0.9934 |
| Decision Tree | 0.9982 | 0.9980 | 0.9976 | 0.9985 | 0.9993 |
| Random Forest | 0.9984 | 0.9983 | 0.9991 | 0.9974 | 1.0000 |
| SVM (Linear, calibrated) | 0.9569 | 0.9533 | 0.9609 | 0.9458 | 0.9931 |
| Neural Network (MLP) | 0.9957 | 0.9953 | 0.9959 | 0.9948 | 0.9998 |
| **XGBoost (baseline)** ★ best by F1 | **0.9993** | **0.9993** | 0.9991 | 0.9994 | 1.0000 |
| XGBoost (tuned, RandomizedSearchCV) | 0.9992 | 0.9991 | 0.9991 | 0.9991 | 1.0000 |
| Stacking Ensemble | 0.9990 | 0.9989 | 0.9990 | 0.9988 | 1.0000 |
| Isolation Forest (honest, unsupervised) | 0.9188 | 0.9124 | 0.9168 | 0.9080 | n/a¹ |
| Isolation Forest (disclosed true-rate benchmark) | 0.7519 | 0.7895 | 0.6523 | 0.9998 | n/a¹ |
| **XGBoost (tuned, recall-favoring threshold = 0.9963)** ★ shipped | 0.9954 | 0.9950 | **1.0000** | 0.9900 | 1.0000 |

¹ Isolation Forest exposes no probability scores, so ROC-AUC can't be computed for it.

**XGBoost tuned hyperparameters:** `subsample=1.0, n_estimators=400, min_child_weight=1, max_depth=6, learning_rate=0.1, colsample_bytree=0.8` (Best CV F1 during search: 0.9989)

### 4.2 Cross-validation — stratified 5-fold (training data)

| Model | CV F1 | CV ROC-AUC |
|---|---|---|
| Logistic Regression | 0.9548 ± 0.0019 | 0.9932 ± 0.0004 |
| Decision Tree | 0.9973 ± 0.0004 | 0.9990 ± 0.0002 |
| Random Forest | 0.9985 ± 0.0001 | 1.0000 ± 0.0000 |
| **XGBoost (tuned)** | **0.9990 ± 0.0002** | **1.0000 ± 0.0000** |

### 4.3 Multi-class classification (attack type) — 14 classes

| Model | Accuracy | Macro F1 | Macro AUC (OVR) |
|---|---|---|---|
| Logistic Regression | 0.9884 | 0.9170 | 0.9991 |
| Decision Tree | 0.9942 | 0.9019 | 0.9721 |
| Random Forest | 0.9986 | 0.9718 | 0.9999 |
| **XGBoost** ★ best | **0.9992** | **0.9757** | 0.9998 |

### 4.4 Unsupervised methods

| Method | Silhouette | Davies-Bouldin | ROC-AUC | Note |
|---|---|---|---|---|
| **K-Means** (QuantileTransformer) ★ best | **0.4438** | 0.9684 | – | alignment=0.884 with true label |
| Hierarchical (Ward linkage) | 0.4319 | 1.0832 | – | alignment=0.881 |
| DBSCAN (auto eps=0.8236) | 0.2805 | 0.8688 | – | 50 clusters, 788 noise points |
| **PCA Reconstruction Error** | – | – | **0.9710** | 15 components, threshold=0.4463 |

**Shipped decision thresholds** (`decision_thresholds.pkl`): `default_threshold=0.5000`,
`recall_favoring_threshold=0.9963` (chosen operating point), `pca_reconstruction_threshold=0.4463`.

---

## 5. Insights & Recommendations

1. **Tree-based/boosted models win decisively** (XGBoost/RF at 0.998+ F1 vs. ~0.95 F1 for linear models) —
   consistent with categorical connection metadata being the strongest statistical signal (§3.2).
2. **Near-perfect ROC-AUC is a benchmark-dataset property, not a live-traffic guarantee** — NSL-KDD's
   attack traffic is behaviorally very distinct from its normal traffic; real production traffic is
   noisier. Re-evaluate at realistic (non-46.5%) assumed anomaly rates before trusting these numbers on
   live traffic.
3. **The shipped threshold (0.9963) isn't the default (0.5)** — tuning for the highest cutoff that still
   holds ≥99% recall buys perfect precision at only a 1-point recall cost vs. the untuned baseline, a much
   better trade-off for a security tool.
4. **The multiclass task is meaningfully harder** than binary (0.9757 vs. 0.9993 F1) — naming the specific
   attack type should be treated as advisory, not authoritative, especially on borderline cases.
5. **PCA Reconstruction Error (0.9710 AUC) earns its place in production** despite using zero labels —
   kept running in parallel specifically as a safety net for attack patterns outside the 23 labeled types.
6. **Formalize H5** with an actual significance test instead of a coefficient-only check.
7. **Automate the VIF/correlation-threshold drop** instead of leaving it print-only, so future feature
   additions can't silently reintroduce severe multicollinearity unnoticed.

---

## 6. Deployment

**Architecture:** Flask REST API (`backend/`) + React/Chart.js dashboard (`frontend/`), serving 4
prediction endpoints (`/predict`, `/predict/attack-type`, `/predict/reconstruction`, `/predict/full`) plus
a live training pipeline triggerable from the UI, streaming logs over Server-Sent Events.

The deployment layer — `Dockerfile`, `docker-compose.yml`, `gunicorn_config.py`, `Procfile`,
`run_container.sh` — lives **directly at the project root**, alongside `app.py` and `run.sh`, so it works
with zero special flags:

```bash
./run_container.sh
```

`run_container.sh` auto-detects whichever container engine you have (Docker or Podman — both were verified
working against this exact repo, see the Podman subsection below), builds the image, starts the container
detached, polls `/health` until it's ready, and opens your browser. `./run_container.sh stop` /
`./run_container.sh logs` / `./run_container.sh status` manage it afterward. It's the containerized
counterpart to the root `run.sh` (which runs Flask's dev server directly, no container) — use `run.sh` for
day-to-day development, `run_container.sh` to run/test the app the way it'd actually run in production.

Or drive the compose tooling directly, without the wrapper script:

```bash
docker build -t network-anomaly-detection .
docker run -p 5000:5000 network-anomaly-detection
```

or

```bash
docker compose up --build      # Docker
podman-compose up --build      # Podman
```

Open **http://localhost:5000**.

**Model artifacts:** if `backend/app/ml_model_pipeline/model_artifacts/` already contains trained `.pkl`
files when you build, the image serves predictions immediately. If not, the app starts in a graceful
"not trained yet" state (`GET /health` → `status: "not_trained"`) — train from the dashboard's **Train
Pipeline** tab or via `docker exec -it <container> python run.py train --data Network_anomaly_data.csv`.
`docker-compose.yml` mounts `model_artifacts/`, `plots/`, and `logs/` as volumes so a container rebuild
doesn't throw away a training run.

### Podman (verified working, no Docker required)

`Dockerfile`/`docker-compose.yml` need zero changes — podman is a drop-in replacement:

```bash
podman machine init && podman machine start   # macOS/Windows only — podman needs a Linux VM; skip on native Linux
podman-compose up -d --build                  # or: podman compose up -d --build, if your podman version bundles it
```

Verified live against this exact repo: image builds, container starts, `/health` reports all 9 artifacts
loaded, and `/predict` returns correct results. Two podman-specific things worth knowing:

- **`HEALTHCHECK` is silently ignored** — podman's default build format is OCI, which doesn't support the
  Dockerfile `HEALTHCHECK` instruction (a Docker-specific extension). Podman prints a harmless warning and
  moves on; the app itself is completely unaffected, only external container-level health monitoring is
  lost. To keep it, build in Docker format instead: `podman build --format docker -t network-anomaly-detection .`
  (or add `format: docker` under `build:` in `docker-compose.yml`, if your podman-compose version supports it).
- **`xgboost`'s Linux wheel pulls in `nvidia-nccl-cu12` (~340 MB) even for CPU-only use** — a known
  upstream packaging quirk (NCCL is xgboost's optional multi-GPU distributed-training backend, but recent
  Linux wheels list it as a hard dependency regardless). It doesn't break anything, but it's most of the
  image's size and build time. If that matters, pin an xgboost build/version without the GPU extra, or
  strip it post-install; not changed here since removing it needs verifying against whatever xgboost
  version you're pinned to.

### Render / Railway / Heroku-style PaaS

These platforms auto-detect `Procfile` at the repository root — it's already there, so no extra copying
or flags are needed. It runs:

```
gunicorn --config gunicorn_config.py app:app
```

Also required for most of these platforms:
1. A Python version pin matching your target platform (developed/validated on Python 3.13; 3.10+ should
   work per `README.md`).
2. Build step: `pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..`
   (or build the frontend locally and commit `frontend/dist/` if the platform has no Node at build time).
3. Set the `PORT` environment variable if the platform doesn't inject one automatically — `app.py` already
   reads it from the environment (defaults to `5000`).

### Bare metal / VM (systemd)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
```

```ini
# /etc/systemd/system/network-anomaly-detection.service
[Unit]
Description=Network Anomaly Detection
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/network-anomaly-detection
Environment=PORT=5000
ExecStart=/opt/network-anomaly-detection/.venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now network-anomaly-detection
```

Put nginx or another reverse proxy in front for TLS termination — gunicorn here binds plain HTTP on
`0.0.0.0:$PORT`.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `0` | Set to `1` only for local debugging — never in production |
| `MODEL_DIR` | `backend/app/ml_model_pipeline/model_artifacts` | Override to point at a different artifacts directory |
| `GUNICORN_WORKERS` | `1` | Worker **process** count — must stay 1 unless training's `_state` tracking is refactored to something shared across processes |
| `GUNICORN_THREADS` | `4` | Threads per worker (`gthread` class) — lets the long-lived training SSE stream run without blocking other concurrent requests |
| `GUNICORN_TIMEOUT` | `1800` | Per-request timeout (seconds) — must exceed the longest silent training step (RandomizedSearchCV can run several minutes with no output) |
| `GUNICORN_LOG_LEVEL` | `info` | Gunicorn's own access/error log verbosity |
| `LOG_LEVEL` | `INFO` | Application log verbosity (`config/logging_config.py`) — set `DEBUG` for verbose output |

### Health check & smoke test

```bash
curl -s http://localhost:5000/health
# {"status":"ok","models_loaded":[...9 artifacts...],"load_errors":{}}

curl -s -X POST http://localhost:5000/predict/full \
  -H "Content-Type: application/json" \
  -d '{"duration":0,"protocoltype":"tcp","service":"private","flag":"S0","srcbytes":0,"dstbytes":0,"land":0,"wrongfragment":0,"urgent":0,"hot":0,"numfailedlogins":0,"loggedin":0,"numcompromised":0,"rootshell":0,"suattempted":0,"numroot":0,"numfilecreations":0,"numshells":0,"numaccessfiles":0,"ishostlogin":0,"isguestlogin":0,"count":123,"srvcount":6,"serrorrate":1.0,"srvserrorrate":1.0,"rerrorrate":0,"srvrerrorrate":0,"samesrvrate":0.05,"diffsrvrate":0.07,"srvdiffhostrate":0,"dsthostcount":255,"dsthostsrvcount":26,"dsthostsamesrvrate":0.10,"dsthostdiffsrvrate":0.05,"dsthostsamesrcportrate":0.0,"dsthostsrvdiffhostrate":0.0,"dsthostserrorrate":1.0,"dsthostsrvserrorrate":1.0,"dsthostrerrorrate":0,"dsthostsrvrerrorrate":0.0}'
```

The Docker image also ships a `HEALTHCHECK` against `/health` (30s interval, 3 retries) so orchestrators
(Docker, Kubernetes, ECS) can detect a stuck container automatically.

### Operational notes

- Model artifacts are loaded into memory **per gunicorn worker process** — with the current `workers=1`
  constraint, that's a single copy; don't raise `GUNICORN_WORKERS` without also solving the
  training-state-sharing problem that would reintroduce (training progress is tracked in a plain
  in-process dict, private to whichever worker process handles it).
- Training is triggered via `POST /api/train/start` and runs as a background subprocess, but its progress
  is streamed back to the client over a **single long-lived SSE HTTP request**
  (`GET /api/train/logs`) that stays open for the entire training run (20–40 minutes on the full dataset —
  SVM, MLP, and the XGBoost hyperparameter search are the slow steps). That request **does** count against
  `GUNICORN_TIMEOUT` — it's sized generously (1800s) specifically to cover this.

---

## Links

- **Notebook:** [`notebooks/Network_Anomaly_Detection_Standalone.ipynb`](notebooks/Network_Anomaly_Detection_Standalone.ipynb)
- **Main project README:** [`README.md`](README.md)
- **GitHub repository:** _add your repo URL here_
- **Live demo:** _add your deployed dashboard URL here_
