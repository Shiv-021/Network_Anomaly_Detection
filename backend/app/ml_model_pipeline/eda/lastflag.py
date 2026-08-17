"""
backend/training/eda/lastflag.py
==================================
Step 2 — Inspect the lastflag column.

lastflag is a difficulty-score artefact embedded in the NSL-KDD dataset,
not a real network feature. Documented here so it is not silently used.
"""
import pandas as pd


def check(df: pd.DataFrame) -> None:
    """Print lastflag stats grouped by attack type."""
    print("\n--- lastflag vs attack (difficulty score, not a real network feature) ---")
    if "lastflag" in df.columns:
        print(df.groupby("attack")["lastflag"].mean().sort_values(ascending=False).head(10))
    else:
        print("lastflag column not present in this dataset.")
