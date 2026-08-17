"""
backend/training/feature_engineering/engineer.py
==================================================
Step 11 — Derive new binary features from raw columns.

Permanent additions  (kept through to df_model)
  is_s0_flag        — flag == 'S0'  (SYN-only scan, strong anomaly signal)
  is_icmp           — protocoltype == 'icmp'
  is_zero_byte_conn — srcbytes==0 AND dstbytes==0

Temporary additions  (dropped by cleanup.drop_redundant in Step 13)
  bytes_ratio        — srcbytes / (dstbytes + 1)  [VIF=415, drops in step 13]
  total_error_rate   — serrorrate + rerrorrate     [linear combo, drops in step 13]
"""
import pandas as pd
from config.columns import ENGINEERED_FEATURES


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return df copy with engineered + temporary columns appended."""
    print("\n" + "=" * 70)
    print("STEP 11: FEATURE ENGINEERING")
    print("=" * 70)
    df = df.copy()

    # Permanent engineered features
    df["is_s0_flag"]        = (df["flag"] == "S0").astype(int)
    df["is_icmp"]           = (df["protocoltype"] == "icmp").astype(int)
    df["is_zero_byte_conn"] = (
        (df["srcbytes"] == 0) & (df["dstbytes"] == 0)
    ).astype(int)

    # Temporary — used for diagnostics, removed in step 13
    df["bytes_ratio"]      = df["srcbytes"] / (df["dstbytes"] + 1)
    df["total_error_rate"] = df["serrorrate"] + df["rerrorrate"]

    print("Zero-byte connection anomaly rate:")
    print(df.groupby("is_zero_byte_conn")["is_anomaly"].mean())

    print("\n--- New feature correlation with is_anomaly ---")
    print(df[ENGINEERED_FEATURES + ["total_error_rate", "is_anomaly"]].corr()["is_anomaly"])
    return df
