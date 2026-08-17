"""
backend/training/feature_engineering/vif.py
=============================================
Step 14 — Variance Inflation Factor (VIF) check.

Computes VIF for a representative subset of retained numeric features.
Values above ~10 indicate concerning multicollinearity.
No files are written; output is printed only.
"""
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

_VIF_CANDIDATES = [
    "duration", "srcbytes", "dstbytes", "count", "srvcount",
    "serrorrate", "srvserrorrate", "rerrorrate", "srvrerrorrate",
    "samesrvrate", "diffsrvrate", "dsthostcount", "dsthostsrvcount",
    "dsthostsamesrvrate", "dsthostserrorrate",
    "is_s0_flag", "is_icmp", "is_zero_byte_conn",
]


def check_vif(df: pd.DataFrame) -> None:
    """Print VIF for each candidate column present in df."""
    candidates = [c for c in _VIF_CANDIDATES if c in df.columns]
    vif_data = df[candidates].copy().replace([np.inf, -np.inf], 0).fillna(0)
    vif_results = pd.DataFrame({
        "feature": candidates,
        "VIF": [
            variance_inflation_factor(vif_data.values.astype(float), i)
            for i in range(len(candidates))
        ],
    })
    print("\n--- VIF — values above ~10 indicate concerning multicollinearity ---")
    print(vif_results.sort_values("VIF", ascending=False).to_string(index=False))
