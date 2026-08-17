"""
backend/training/feature_engineering/distributions.py
=======================================================
Step 12 — Full numeric distribution grid (post-engineering diagnostic plot).

Plots histograms for every numeric column except diagnostic/target columns.
Saved to plots/full_distribution_grid.png.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

# Columns to skip: intermediates, targets, log-transforms, flags
_SKIP = {
    "is_anomaly", "bytes_ratio", "total_error_rate",
    "srcbytes_log", "dstbytes_log", "duration_log",
}


def plot_grid(df: pd.DataFrame, savefig) -> None:
    """Save a histogram grid for all retained numeric columns."""
    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if not c.startswith("is_") and c not in _SKIP
    ]
    n_cols = 6
    n_rows = int(np.ceil(len(numeric_cols) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(24, 4 * n_rows))
    axes = axes.flatten()
    for i, col in enumerate(numeric_cols):
        sns.histplot(df[col], bins=30, ax=axes[i])
        axes[i].set_title(col, fontsize=9)
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    plt.tight_layout()
    savefig("full_distribution_grid.png")
    print(f"Plotted distributions for {len(numeric_cols)} numeric columns.")
