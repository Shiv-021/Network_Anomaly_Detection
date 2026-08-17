"""
backend/training/feature_engineering/__init__.py
==================================================
Feature engineering pipeline orchestrator.

Imports one function from each step module and calls them in sequence.
Add or remove a step by editing the imports and the call list in
engineer_and_select() — nothing else needs to change.

Step modules
------------
  engineer.py       Step 11 — add is_s0_flag, is_icmp, is_zero_byte_conn
                              (+ temporary bytes_ratio, total_error_rate)
  distributions.py  Step 12 — full numeric distribution grid (diagnostic plot)
  cleanup.py        Step 13 — drop redundant/zero-variance columns
  vif.py            Step 14 — VIF multicollinearity check
  heatmap.py        Step 15 — final post-engineering correlation heatmap
  selector.py       Step 16 — select final modeling feature set → df_model

Public API
----------
    df_model = engineer_and_select(df_annotated, save_plots=True, plot_dir="plots")
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .engineer      import add_features
from .distributions import plot_grid
from .cleanup       import drop_redundant
from .vif           import check_vif
from .heatmap       import plot_heatmap
from .selector      import select_features


def engineer_and_select(
    df: pd.DataFrame,
    save_plots: bool = True,
    plot_dir: str = "plots",
) -> pd.DataFrame:
    """
    Apply feature engineering and return the modeling-ready DataFrame.

    Parameters
    ----------
    df         : DataFrame returned by eda.run_eda().
    save_plots : write PNG files to plot_dir when True.
    plot_dir   : directory for output plots.

    Returns
    -------
    pd.DataFrame — df_model passed directly to trainer.train_all().
    """
    print("\n" + "=" * 70)
    print("BLOCK 2 (FEATURE ENGINEERING): STEPS 11-16")
    print("=" * 70)

    os.makedirs(plot_dir, exist_ok=True)

    def savefig(name: str) -> None:
        if save_plots:
            plt.savefig(os.path.join(plot_dir, name), dpi=100, bbox_inches="tight")
        plt.close()

    df        = add_features(df)
    plot_grid(df, savefig)
    df        = drop_redundant(df)
    check_vif(df)
    plot_heatmap(df, savefig)
    df_model  = select_features(df)

    print(f"\ndf_model shape (ready for Block 3): {df_model.shape}")
    print("Block 2 (feature engineering) complete.")
    return df_model
