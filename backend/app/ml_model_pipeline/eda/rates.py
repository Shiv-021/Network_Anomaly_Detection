"""
backend/training/eda/rates.py
================================
Step 8 — Histograms for the eight rate-based features.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

_RATE_COLS = [
    "serrorrate", "srvserrorrate", "rerrorrate", "srvrerrorrate",
    "samesrvrate", "diffsrvrate", "dsthostsamesrvrate", "dsthostserrorrate",
]


def plot(df: pd.DataFrame, savefig) -> None:
    """Plot histograms for all rate features present in df."""
    fig, axes = plt.subplots(2, 4, figsize=(20, 8))
    for i, col in enumerate(_RATE_COLS):
        if col in df.columns:
            sns.histplot(df[col], bins=30, ax=axes[i // 4][i % 4])
            axes[i // 4][i % 4].set_title(col)
    plt.tight_layout()
    savefig("rate_feature_distributions.png")
