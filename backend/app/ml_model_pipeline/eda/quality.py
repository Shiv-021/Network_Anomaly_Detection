"""
backend/training/eda/quality.py
=================================
Step 6 — Missing value audit and exact duplicate row removal.
"""
import pandas as pd


def check(df: pd.DataFrame) -> pd.DataFrame:
    """Print missing value counts and remove exact duplicate rows."""
    print("\n--- Missing values ---")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "(none found)")

    print("\n--- Duplicate rows ---")
    n_dupes = df.duplicated().sum()
    print(f"Fully duplicated rows: {n_dupes} ({n_dupes / len(df) * 100:.2f}%)")
    if n_dupes > 0:
        print("Dropping exact duplicate rows.")
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"Shape after dedup: {df.shape}")
    return df
