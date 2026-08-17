"""
backend/training/eda/__init__.py
=================================
EDA pipeline orchestrator.

Imports one function from each step module and runs them in sequence
inside run_eda().  Add or remove a step by editing the imports and the
single call in run_eda() — nothing else needs to change.

Step modules
------------
  target.py            Step 1  — binary target creation + class plots
  lastflag.py          Step 2  — lastflag artefact inspection
  numeric.py           Step 3  — numeric distributions + log transforms
  hypothesis_tests.py  Step 4  — five statistical hypothesis tests
  correlations.py      Step 5  — correlation heatmap
  quality.py           Step 6  — missing values + deduplication
  categorical.py       Step 7  — categorical column distributions
  rates.py             Step 8  — rate-feature histograms
  outliers.py             Step 9  — IQR outlier detection + flag column
  timeseries.py           Step 10 — temporal proxy analysis + plots
  security_indicators.py  Step 11 — security-indicator features stratified by class

Public API
----------
    df_annotated, stats = run_eda(df, save_plots=True, plot_dir="plots")
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .target           import analyze   as _step1
from .lastflag         import check     as _step2
from .numeric          import analyze   as _step3
from .hypothesis_tests import run_tests as _step4
from .correlations     import plot      as _step5
from .quality          import check     as _step6
from .categorical      import plot      as _step7
from .rates            import plot      as _step8
from .outliers              import detect    as _step9
from .timeseries            import analyze   as _step10
from .security_indicators   import plot      as _step11


def run_eda(
    df: pd.DataFrame,
    save_plots: bool = True,
    plot_dir: str = "plots",
) -> tuple[pd.DataFrame, dict]:
    """
    Run the full EDA pipeline on a raw NSL-KDD DataFrame.

    Parameters
    ----------
    df         : raw DataFrame from data_loader.load_data().
    save_plots : write PNG files to plot_dir when True.
    plot_dir   : directory for output plots.

    Returns
    -------
    (df_annotated, stats_dict)
        df_annotated — df with is_anomaly, log features, outlier flag added
                       and exact duplicates removed.
        stats_dict   — p-values, anomaly rate, and temporal findings.
    """
    print("\n" + "=" * 70)
    print("BLOCK 2 (EDA): EXPLORATORY DATA ANALYSIS")
    print("=" * 70)

    os.makedirs(plot_dir, exist_ok=True)

    def savefig(name: str) -> None:
        if save_plots:
            plt.savefig(os.path.join(plot_dir, name), dpi=100, bbox_inches="tight")
        plt.close()

    collected: dict = {}

    df, s = _step1(df, savefig)
    collected.update(s)

    _step2(df)
    df  = _step3(df, savefig)
    ht  = _step4(df)
    collected.update(ht)
    _step5(df, savefig)
    df  = _step6(df)
    _step7(df, savefig)
    _step8(df, savefig)
    df  = _step9(df, savefig)
    ts  = _step10(df, savefig)
    collected.update(ts)
    _step11(df, savefig)

    print("\nBlock 2 (EDA) complete.")
    return df, collected
