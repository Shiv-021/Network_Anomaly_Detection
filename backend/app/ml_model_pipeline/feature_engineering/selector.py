"""
backend/training/feature_engineering/selector.py
==================================================
Step 16 — Select the final modeling feature set.

Reads column lists from config.columns so the selection stays in sync with
the inference preprocessor (backend/core/preprocessor.py) automatically.
Any column listed but absent from df is silently skipped (guards against
dataset variants that omit some columns).
"""
import pandas as pd
from config.columns import MODELING_INPUT_COLS, TARGET_COLS, ENGINEERED_FEATURES

# Guard: detect drift between config.columns and what engineer.py actually produces.
# Fails loudly at training time rather than silently mismatching feature order.
_EXPECTED_ENGINEERED = set(ENGINEERED_FEATURES)


def _assert_engineered_present(df: pd.DataFrame) -> None:
    missing = _EXPECTED_ENGINEERED - set(df.columns)
    if missing:
        raise ValueError(
            f"selector: expected engineered features {missing} to be present in df "
            f"but they are missing. Check engineer.py and config/columns.py are in sync."
        )


def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return df filtered to exactly the columns needed for training.
    Column order matches MODELING_INPUT_COLS + TARGET_COLS from config.columns.
    Raises ValueError if engineered features expected by config.columns are absent.
    """
    _assert_engineered_present(df)
    keep = [c for c in MODELING_INPUT_COLS if c in df.columns]
    print(f"\n--- STEP 16: FEATURE SELECTION ---")
    print(f"Retained {len(keep)} modeling columns + {len(TARGET_COLS)} targets.")
    return df[keep + TARGET_COLS].copy()
