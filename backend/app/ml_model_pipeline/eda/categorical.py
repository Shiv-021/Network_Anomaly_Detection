"""
backend/training/eda/categorical.py
=====================================
Step 7 — Bar-chart distributions for protocoltype, flag, and service (top 15).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot(df: pd.DataFrame, savefig) -> None:
    """Save bar charts for the three categorical columns."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    df["protocoltype"].value_counts().plot(kind="bar", ax=axes[0])
    axes[0].set_title("protocoltype distribution")
    df["flag"].value_counts().plot(kind="bar", ax=axes[1])
    axes[1].set_title("flag distribution")
    df["service"].value_counts().head(15).plot(kind="bar", ax=axes[2])
    axes[2].set_title("service distribution (top 15)")
    plt.tight_layout()
    savefig("categorical_distributions.png")
