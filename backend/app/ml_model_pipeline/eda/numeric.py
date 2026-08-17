"""
backend/training/eda/numeric.py
=================================
Step 3 — Numeric feature distributions (skew check) and log transforms.

Appends srcbytes_log, dstbytes_log, duration_log to the returned DataFrame.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

_PLOT_COLS = ["duration", "srcbytes", "dstbytes", "count", "srvcount"]
_LOG_COLS  = ["srcbytes", "dstbytes", "duration"]


def analyze(df: pd.DataFrame, savefig) -> pd.DataFrame:
    """
    Plot raw distributions and add log-transformed variants.
    Returns updated df with *_log columns appended.
    """
    fig, axes = plt.subplots(1, len(_PLOT_COLS), figsize=(20, 4))
    for i, col in enumerate(_PLOT_COLS):
        if col in df.columns:
            sns.histplot(df[col], bins=50, ax=axes[i])
            axes[i].set_title(f"{col} (skew={df[col].skew():.2f})")
    plt.tight_layout()
    savefig("numeric_distributions.png")

    df = df.copy()
    for col in _LOG_COLS:
        if col in df.columns:
            df[f"{col}_log"] = np.log1p(df[col])
    return df
