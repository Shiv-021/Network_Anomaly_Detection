"""
tests/test_feature_engineering.py
===================================
Unit tests for the feature engineering pipeline steps.

Run with:
    python -m pytest tests/ -v
    python -m pytest tests/test_feature_engineering.py -v
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.ml_model_pipeline.feature_engineering.engineer import add_features
from backend.app.ml_model_pipeline.feature_engineering.cleanup import drop_redundant
from backend.app.ml_model_pipeline.feature_engineering.selector import (
    select_features,
    _assert_engineered_present,
)
from config.columns import MODELING_INPUT_COLS, TARGET_COLS, ENGINEERED_FEATURES

# ---------------------------------------------------------------------------
# Minimal synthetic DataFrame that mirrors the post-EDA structure
# ---------------------------------------------------------------------------

def _make_df(n=10):
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "duration":               rng.integers(0, 100, n),
        "protocoltype":           rng.choice(["tcp", "udp", "icmp"], n),
        "service":                rng.choice(["http", "ftp", "private"], n),
        "flag":                   rng.choice(["SF", "S0", "REJ"], n),
        "srcbytes":               rng.integers(0, 50000, n),
        "dstbytes":               rng.integers(0, 50000, n),
        "land":                   rng.integers(0, 2, n),
        "wrongfragment":          rng.integers(0, 5, n),
        "urgent":                 rng.integers(0, 2, n),
        "hot":                    rng.integers(0, 10, n),
        "numfailedlogins":        rng.integers(0, 3, n),
        "loggedin":               rng.integers(0, 2, n),
        "numcompromised":         rng.integers(0, 5, n),
        "rootshell":              rng.integers(0, 2, n),
        "suattempted":            rng.integers(0, 2, n),
        "numroot":                rng.integers(0, 5, n),
        "numfilecreations":       rng.integers(0, 5, n),
        "numshells":              rng.integers(0, 3, n),
        "numaccessfiles":         rng.integers(0, 3, n),
        "ishostlogin":            rng.integers(0, 2, n),
        "isguestlogin":           rng.integers(0, 2, n),
        "count":                  rng.integers(1, 512, n),
        "srvcount":               rng.integers(1, 512, n),
        "serrorrate":             rng.random(n),
        "srvserrorrate":          rng.random(n),
        "rerrorrate":             rng.random(n),
        "srvrerrorrate":          rng.random(n),
        "samesrvrate":            rng.random(n),
        "diffsrvrate":            rng.random(n),
        "srvdiffhostrate":        rng.random(n),
        "dsthostcount":           rng.integers(1, 256, n),
        "dsthostsrvcount":        rng.integers(1, 256, n),
        "dsthostsamesrvrate":     rng.random(n),
        "dsthostdiffsrvrate":     rng.random(n),
        "dsthostsamesrcportrate": rng.random(n),
        "dsthostsrvdiffhostrate": rng.random(n),
        "dsthostserrorrate":      rng.random(n),
        "dsthostsrvserrorrate":   rng.random(n),
        "dsthostrerrorrate":      rng.random(n),
        "dsthostsrvrerrorrate":   rng.random(n),
        # Annotation columns added by EDA
        "is_anomaly":             rng.integers(0, 2, n),
        "attack":                 rng.choice(["normal", "neptune", "smurf"], n),
        "is_srcbytes_outlier":    rng.integers(0, 2, n),
        "srcbytes_log":           np.log1p(rng.integers(0, 50000, n).astype(float)),
        "dstbytes_log":           np.log1p(rng.integers(0, 50000, n).astype(float)),
        "duration_log":           np.log1p(rng.integers(0, 100, n).astype(float)),
    })
    return df


# ---------------------------------------------------------------------------
# add_features (Step 11)
# ---------------------------------------------------------------------------

class TestAddFeatures:

    def test_returns_copy_not_mutating_input(self):
        df = _make_df()
        original_cols = set(df.columns)
        add_features(df)
        assert set(df.columns) == original_cols  # original unchanged

    def test_adds_all_engineered_features(self):
        df = _make_df()
        result = add_features(df)
        for feat in ENGINEERED_FEATURES:
            assert feat in result.columns, f"Missing engineered feature: {feat}"

    def test_adds_temporary_features(self):
        df = _make_df()
        result = add_features(df)
        assert "bytes_ratio" in result.columns
        assert "total_error_rate" in result.columns

    def test_is_s0_flag_correct(self):
        df = _make_df(4)
        df["flag"] = ["SF", "S0", "S0", "REJ"]
        result = add_features(df)
        assert list(result["is_s0_flag"]) == [0, 1, 1, 0]

    def test_is_icmp_correct(self):
        df = _make_df(3)
        df["protocoltype"] = ["tcp", "icmp", "udp"]
        result = add_features(df)
        assert list(result["is_icmp"]) == [0, 1, 0]

    def test_is_zero_byte_conn_correct(self):
        df = _make_df(3)
        df["srcbytes"] = [0, 0, 10]
        df["dstbytes"] = [0, 5, 0]
        result = add_features(df)
        assert list(result["is_zero_byte_conn"]) == [1, 0, 0]

    def test_output_values_are_binary(self):
        df = _make_df(50)
        result = add_features(df)
        for col in ["is_s0_flag", "is_icmp", "is_zero_byte_conn"]:
            assert set(result[col].unique()).issubset({0, 1})


# ---------------------------------------------------------------------------
# drop_redundant (Step 13)
# ---------------------------------------------------------------------------

class TestDropRedundant:

    def test_drops_total_error_rate(self):
        df = add_features(_make_df())
        result = drop_redundant(df)
        assert "total_error_rate" not in result.columns

    def test_drops_bytes_ratio(self):
        df = add_features(_make_df())
        result = drop_redundant(df)
        assert "bytes_ratio" not in result.columns

    def test_drops_zero_variance_numoutboundcmds(self):
        df = add_features(_make_df())
        df["numoutboundcmds"] = 0  # constant — all zeros
        result = drop_redundant(df)
        assert "numoutboundcmds" not in result.columns

    def test_keeps_numoutboundcmds_if_has_variance(self):
        df = add_features(_make_df())
        df["numoutboundcmds"] = list(range(len(df)))  # has variance
        result = drop_redundant(df)
        assert "numoutboundcmds" in result.columns

    def test_engineered_features_survive(self):
        df = add_features(_make_df())
        result = drop_redundant(df)
        for feat in ENGINEERED_FEATURES:
            assert feat in result.columns


# ---------------------------------------------------------------------------
# select_features (Step 16)
# ---------------------------------------------------------------------------

class TestSelectFeatures:

    def _engineered_df(self):
        df = _make_df()
        df = add_features(df)
        df = drop_redundant(df)
        return df

    def test_output_contains_targets(self):
        df = self._engineered_df()
        result = select_features(df)
        for t in TARGET_COLS:
            assert t in result.columns

    def test_output_does_not_contain_extra_cols(self):
        df = self._engineered_df()
        result = select_features(df)
        allowed = set(MODELING_INPUT_COLS) | set(TARGET_COLS)
        unexpected = set(result.columns) - allowed
        assert not unexpected, f"Unexpected columns in output: {unexpected}"

    def test_raises_if_engineered_features_missing(self):
        df = _make_df()  # no add_features called → no engineered cols
        with pytest.raises(ValueError, match="engineered features"):
            select_features(df)

    def test_output_row_count_unchanged(self):
        df = self._engineered_df()
        result = select_features(df)
        assert len(result) == len(df)


# ---------------------------------------------------------------------------
# config.columns consistency check
# ---------------------------------------------------------------------------

class TestColumnsConfig:

    def test_modeling_input_cols_contains_all_engineered(self):
        for feat in ENGINEERED_FEATURES:
            assert feat in MODELING_INPUT_COLS, (
                f"{feat} is in ENGINEERED_FEATURES but missing from MODELING_INPUT_COLS"
            )

    def test_no_target_cols_in_modeling_input_cols(self):
        for t in TARGET_COLS:
            assert t not in MODELING_INPUT_COLS, (
                f"{t} is a target but also appears in MODELING_INPUT_COLS"
            )

    def test_no_duplicate_modeling_input_cols(self):
        assert len(MODELING_INPUT_COLS) == len(set(MODELING_INPUT_COLS)), \
            "MODELING_INPUT_COLS contains duplicate entries"
