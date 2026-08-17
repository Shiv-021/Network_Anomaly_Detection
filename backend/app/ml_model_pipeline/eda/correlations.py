"""
backend/training/eda/correlations.py
=======================================
Step 5 — Pre-engineering correlation heatmap of all numeric features.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")


def plot(df: pd.DataFrame, savefig) -> None:
    """Save a full correlation heatmap to plots/correlation_heatmap.png."""
    numeric_df = df.select_dtypes(include=[np.number])
    plt.figure(figsize=(18, 14))
    sns.heatmap(numeric_df.corr(), cmap="coolwarm", center=0, annot=False)
    plt.title("Correlation Heatmap — Numeric Features (pre-engineering)")
    plt.tight_layout()
    savefig("correlation_heatmap.png")
