"""
backend/app/train.py — Network Anomaly Detection Training Pipeline
===================================================================
Entry point that runs the full training workflow end-to-end by delegating
to the focused modules under backend/app/ml_model_pipeline/:

    ml_model_pipeline/data_loader.py          Block 1 — load CSV (local-first)
    ml_model_pipeline/eda/                    Block 2a — EDA, cleaning
    ml_model_pipeline/feature_engineering/   Block 2b — feature engineering
    ml_model_pipeline/trainer/               Block 3  — ML training, artifact saving

Usage
-----
    python backend/app/train.py                              # auto-download from Google Drive
    python backend/app/train.py --data Network_anomaly_data.csv   # use local CSV (preferred)
    python backend/app/train.py --no-plots                   # skip saving plots (faster)

    python main.py train --data Network_anomaly_data.csv     # via root CLI orchestrator

Artifacts saved
    backend/app/ml_model_pipeline/model_artifacts/   9 .pkl files consumed by app.py
    plots/                                           EDA + modelling plots (unless --no-plots)
"""

import argparse
import sys
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths — resolved centrally from config.settings
# ---------------------------------------------------------------------------
import os
# This file lives at <root>/backend/app/ml_model_pipeline/train.py -- four
# directory levels below <root> (backend, app, ml_model_pipeline, then the
# file itself), so reaching <root> needs FOUR os.path.dirname() calls, not
# three. The previous 3-call version landed one level short, at <root>/backend
# (which has no config/ package), raising "ModuleNotFoundError: No module
# named 'config'". That was silently masked whenever this script's subprocess
# happened to inherit a PYTHONPATH with an empty/cwd-implying entry from
# whatever shell started the server -- surfaces reliably in a clean
# environment (e.g. a container) with no such accidental workaround.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.settings import PROJECT_ROOT, MODEL_DIR, PLOT_DIR

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR,  exist_ok=True)

# ---------------------------------------------------------------------------
# CLI — parse before importing heavy training modules
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Network Anomaly Detection — Training Pipeline")
parser.add_argument("--data",     default=None, help="Path to local CSV (skips Google Drive download)")
parser.add_argument("--no-plots", action="store_true", help="Skip saving plots (headless mode)")
args = parser.parse_args()

SAVE_PLOTS = not args.no_plots

# ---------------------------------------------------------------------------
# Training modules
# ---------------------------------------------------------------------------
from backend.app.ml_model_pipeline.data_loader           import load_data
from backend.app.ml_model_pipeline.eda                   import run_eda
from backend.app.ml_model_pipeline.feature_engineering   import engineer_and_select
from backend.app.ml_model_pipeline.trainer               import train_all

# =============================================================================
# BLOCK 1: DATA LOAD
# =============================================================================
df = load_data(csv_path=args.data, project_dir=PROJECT_ROOT)

# =============================================================================
# BLOCK 2a: EDA
# =============================================================================
df, eda_stats = run_eda(df, save_plots=SAVE_PLOTS, plot_dir=PLOT_DIR)

# =============================================================================
# BLOCK 2b: FEATURE ENGINEERING
# =============================================================================
df_model = engineer_and_select(df, save_plots=SAVE_PLOTS, plot_dir=PLOT_DIR)

# Save the clean modeling dataset for reference / debugging (to plots dir, not model_artifacts)
df_model.to_csv(os.path.join(PLOT_DIR, "df_model.csv"), index=False)
print(f"\nSaved modeling dataset → {PLOT_DIR}/df_model.csv")

# =============================================================================
# BLOCK 3: ML TRAINING
# =============================================================================
summary = train_all(df_model, model_dir=MODEL_DIR, save_plots=SAVE_PLOTS, plot_dir=PLOT_DIR)

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("TRAINING COMPLETE — SUMMARY")
print("=" * 70)
print(f"""
DATA
  Records (after dedup)  : {len(df)}
  Anomaly rate           : {df['is_anomaly'].mean()*100:.2f}%
  Distinct attack types  : {df['attack'].nunique()}
  Modeling features      : {len(df_model.columns) - 2}

HYPOTHESIS TESTS
  srcbytes      p={eda_stats.get('srcbytes_pval', float('nan')):.6f}
  protocoltype  p={eda_stats.get('protocoltype_pval', float('nan')):.6f}
  service       p={eda_stats.get('service_pval', float('nan')):.6f}
  flag          p={eda_stats.get('flag_pval', float('nan')):.6f}

SUPERVISED — BINARY (is_anomaly)
  Best by F1               : {summary['best_binary_model']}
  Recall-favoring threshold: {summary['chosen_threshold']:.4f}

SUPERVISED — MULTI-CLASS (attack type)
  Classes                  : {summary['n_attack_classes']} (rare types → 'other_rare')
  Best Macro F1            : {summary['best_multiclass_model']}

UNSUPERVISED
  PCA Reconstruction Error AUC: {summary['recon_auc']:.4f}

ARTIFACTS  → {MODEL_DIR}
PLOTS      → {PLOT_DIR}

Ready to serve:
  python app.py
  python run.py serve
""")
