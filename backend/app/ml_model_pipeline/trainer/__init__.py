"""
backend/training/trainer/__init__.py
======================================
Trainer package orchestrator.

Imports one function from each step module and runs them in sequence
inside train_all().  Add or remove a step by editing the imports and the
single call sequence in train_all() — nothing else needs to change.

Step modules
------------
  state.py             TrainingState — shared mutable context
  splitter.py          Step 1  — one-hot encode, train/test split, scale
  binary_models.py     Step 2  — binary supervised models (LR, DT, RF, SVM, MLP, XGB, Stack)
  cross_validation.py  Step 3  — stratified 5-fold cross-validation
  threshold.py         Step 4  — decision threshold tuning
  isolation_forest.py  Step 5  — Isolation Forest (honest + benchmark)
  binary_summary.py    Step 6  — model comparison table + confusion matrices + ROC
  multiclass.py               Step 7  — multi-class attack-type classification
  unsupervised.py             Step 8  — clustering: K-Means / DBSCAN / Hierarchical
  dimensionality_reduction.py Step 8a — PCA projection / t-SNE / PCA reconstruction
                                         error (called from unsupervised.py, kept in
                                         its own file since it's a different technique
                                         from clustering — see module docstring)
  artifacts.py                Step 9  — save .pkl artifacts to models/

Public API
----------
    summary = train_all(df_model, model_dir="models",
                        save_plots=True, plot_dir="plots")
"""

import os
import pandas as pd

from .state            import TrainingState
from .splitter         import prepare_splits
from .binary_models    import train_binary
from .cross_validation import run_cross_validation
from .threshold        import tune_threshold
from .isolation_forest import train_isolation_forest
from .binary_summary   import summarize_binary
from .multiclass       import train_multiclass
from .unsupervised     import train_unsupervised
from .artifacts        import save_artifacts, build_summary


def train_all(
    df_model: pd.DataFrame,
    model_dir: str = "models",
    save_plots: bool = True,
    plot_dir: str = "plots",
) -> dict:
    """
    Run the complete training pipeline and save all artifacts.

    Parameters
    ----------
    df_model   : output of feature_engineering.engineer_and_select().
    model_dir  : directory where .pkl artifacts are saved.
    save_plots : write PNG files to plot_dir when True.
    plot_dir   : directory for output plots.

    Returns
    -------
    dict — summary metrics for the final printout in train.py.
    """
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(plot_dir,  exist_ok=True)

    state = TrainingState(df_model, model_dir, save_plots, plot_dir)

    print("\n" + "=" * 70)
    print("BLOCK 3: ML MODELING")
    print("=" * 70)

    prepare_splits(state)
    train_binary(state)
    run_cross_validation(state)
    tune_threshold(state)
    train_isolation_forest(state)
    binary_info = summarize_binary(state)
    train_multiclass(state)
    train_unsupervised(state)
    save_artifacts(state)
    return build_summary(state, binary_info)
