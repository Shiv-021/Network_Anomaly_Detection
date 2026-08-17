"""
backend/training/feature_engineering/heatmap.py
==================================================
Step 15 — Final post-engineering correlation heatmap.

Excludes diagnostic/log-transform columns that are no longer needed after
feature selection, so the heatmap shows only the retained modeling columns.
Saved to plots/final_correlation_heatmap.png.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

# Columns that exist on df at this stage but are excluded from the heatmap
_EXCLUDE = {"srcbytes_log", "dstbytes_log", "duration_log", "is_srcbytes_outlier"}


def plot_heatmap(df: pd.DataFrame, savefig) -> None:
    """Save a correlation heatmap for all retained numeric columns."""
    final_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in _EXCLUDE
    ]
    plt.figure(figsize=(20, 16))
    sns.heatmap(df[final_cols].corr(), cmap="coolwarm", center=0, annot=False)
    plt.title("Final Correlation Heatmap — Original + Engineered Features")
    plt.tight_layout()
    savefig("final_correlation_heatmap.png")
