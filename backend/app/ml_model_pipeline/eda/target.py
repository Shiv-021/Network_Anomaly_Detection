"""
backend/training/eda/target.py
================================
Step 1 — Create the binary is_anomaly target column and plot class distribution.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def analyze(df: pd.DataFrame, savefig) -> tuple[pd.DataFrame, dict]:
    """Add is_anomaly column and save class-imbalance plots."""
    print("\n--- Attack class distribution ---")
    print(df["attack"].value_counts())
    print("\nAs %:")
    print(df["attack"].value_counts(normalize=True) * 100)

    df = df.copy()
    df["is_anomaly"] = (df["attack"] != "normal").astype(int)

    print("\n--- Binary target distribution ---")
    print(df["is_anomaly"].value_counts())
    print(df["is_anomaly"].value_counts(normalize=True) * 100)

    plt.figure(figsize=(6, 4))
    df["is_anomaly"].value_counts().plot(kind="bar")
    plt.title("Normal (0) vs Anomaly (1) — Class Imbalance")
    plt.xticks([0, 1], ["Normal", "Anomaly"], rotation=0)
    plt.tight_layout()
    savefig("class_imbalance.png")

    plt.figure(figsize=(10, 5))
    df["attack"].value_counts().head(10).plot(kind="bar")
    plt.title("Top 10 Attack Types (including normal)")
    plt.tight_layout()
    savefig("attack_types.png")

    return df, {"anomaly_rate": float(df["is_anomaly"].mean())}
