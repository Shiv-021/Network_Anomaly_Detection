"""
backend/training/eda/outliers.py
==================================
Step 9 — IQR-based outlier detection for key numeric columns.

Appends is_srcbytes_outlier flag column to the returned DataFrame.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

_OUTLIER_COLS = ["duration", "srcbytes", "dstbytes", "count", "srvcount"]


def _iqr_summary(series: pd.Series, name: str) -> pd.Series:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr    = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    out = series[(series < lower) | (series > upper)]
    print(
        f"{name}: {len(out)} outliers ({len(out) / len(series) * 100:.2f}%), "
        f"bounds=({lower:.1f}, {upper:.1f}), max={series.max()}"
    )
    return out


def detect(df: pd.DataFrame, savefig) -> pd.DataFrame:
    """
    Run IQR outlier detection, save box-plots, and append is_srcbytes_outlier
    column. Returns the updated DataFrame.
    """
    print("\n" + "=" * 70)
    print("OUTLIER DETECTION (IQR method)")
    print("=" * 70)
    cols_present = [c for c in _OUTLIER_COLS if c in df.columns]
    outlier_map: dict = {col: _iqr_summary(df[col], col) for col in cols_present}

    fig, axes = plt.subplots(1, len(cols_present), figsize=(20, 4))
    if len(cols_present) == 1:
        axes = [axes]
    for i, col in enumerate(cols_present):
        sns.boxplot(y=df[col], ax=axes[i])
        axes[i].set_title(col)
    plt.tight_layout()
    savefig("outlier_boxplots.png")

    print("\n--- Anomaly rate: srcbytes outliers vs non-outliers ---")
    if "srcbytes" in outlier_map:
        df = df.copy()
        df["is_srcbytes_outlier"] = df.index.isin(outlier_map["srcbytes"].index)
        print(df.groupby("is_srcbytes_outlier")["is_anomaly"].mean())
    return df
