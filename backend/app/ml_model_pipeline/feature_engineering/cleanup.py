"""
backend/training/feature_engineering/cleanup.py
=================================================
Step 13 — Drop redundant and zero-variance columns.

Removed columns
  total_error_rate   — linear combo of serrorrate + rerrorrate (redundant)
  bytes_ratio        — VIF=415, near-zero correlation with is_anomaly (≈0.006)
  numoutboundcmds    — zero variance in NSL-KDD (constant=0 for all rows)
"""
import pandas as pd


def drop_redundant(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with the three redundant columns removed."""
    df = df.drop(columns=["total_error_rate"])
    print("\nDropped total_error_rate (redundant: serrorrate + rerrorrate).")

    df = df.drop(columns=["bytes_ratio"])
    print("Dropped bytes_ratio (VIF=415, correlation with is_anomaly ≈ 0.006).")

    if "numoutboundcmds" in df.columns and df["numoutboundcmds"].nunique() <= 1:
        df = df.drop(columns=["numoutboundcmds"])
        print("Dropped numoutboundcmds (zero variance — constant column).")
    return df
