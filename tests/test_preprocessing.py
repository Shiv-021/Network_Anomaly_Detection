"""
tests/test_preprocessing.py
============================
Unit tests for the inference-time preprocessing pipeline.

Run with:
    python -m pytest tests/ -v
    python -m pytest tests/test_preprocessing.py -v
"""
import sys
import os
import pytest
import pandas as pd

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.ml_model_pipeline.preprocessing.preprocessor import (
    validate_records,
    engineer_features,
    encode_service,
    PreprocessingError,
)
from config.columns import NUMERIC_FEATURES, REQUIRED_FIELDS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_RECORD = {
    "duration": 0, "protocoltype": "tcp", "service": "http", "flag": "SF",
    "srcbytes": 232, "dstbytes": 8153, "land": 0, "wrongfragment": 0, "urgent": 0,
    "hot": 0, "numfailedlogins": 0, "loggedin": 1, "numcompromised": 0,
    "rootshell": 0, "suattempted": 0, "numroot": 0, "numfilecreations": 0,
    "numshells": 0, "numaccessfiles": 0, "ishostlogin": 0, "isguestlogin": 0,
    "count": 5, "srvcount": 5, "serrorrate": 0.0, "srvserrorrate": 0.0,
    "rerrorrate": 0.0, "srvrerrorrate": 0.0, "samesrvrate": 1.0, "diffsrvrate": 0.0,
    "srvdiffhostrate": 0.0, "dsthostcount": 30, "dsthostsrvcount": 255,
    "dsthostsamesrvrate": 1.0, "dsthostdiffsrvrate": 0.0,
    "dsthostsamesrcportrate": 0.03, "dsthostsrvdiffhostrate": 0.04,
    "dsthostserrorrate": 0.03, "dsthostsrvserrorrate": 0.01,
    "dsthostrerrorrate": 0.0, "dsthostsrvrerrorrate": 0.01,
}

NEPTUNE_RECORD = {
    "duration": 0, "protocoltype": "tcp", "service": "private", "flag": "S0",
    "srcbytes": 0, "dstbytes": 0, "land": 0, "wrongfragment": 0, "urgent": 0,
    "hot": 0, "numfailedlogins": 0, "loggedin": 0, "numcompromised": 0,
    "rootshell": 0, "suattempted": 0, "numroot": 0, "numfilecreations": 0,
    "numshells": 0, "numaccessfiles": 0, "ishostlogin": 0, "isguestlogin": 0,
    "count": 123, "srvcount": 6, "serrorrate": 1.0, "srvserrorrate": 1.0,
    "rerrorrate": 0.0, "srvrerrorrate": 0.0, "samesrvrate": 0.05,
    "diffsrvrate": 0.07, "srvdiffhostrate": 0.0, "dsthostcount": 255,
    "dsthostsrvcount": 26, "dsthostsamesrvrate": 0.10, "dsthostdiffsrvrate": 0.05,
    "dsthostsamesrcportrate": 0.0, "dsthostsrvdiffhostrate": 0.0,
    "dsthostserrorrate": 1.0, "dsthostsrvserrorrate": 1.0,
    "dsthostrerrorrate": 0.0, "dsthostsrvrerrorrate": 0.0,
}

# ---------------------------------------------------------------------------
# validate_records
# ---------------------------------------------------------------------------

class TestValidateRecords:

    def test_valid_single_record_passes(self):
        validate_records([MINIMAL_RECORD])  # must not raise

    def test_valid_batch_passes(self):
        validate_records([MINIMAL_RECORD, NEPTUNE_RECORD])

    def test_empty_list_raises(self):
        with pytest.raises(PreprocessingError, match="non-empty list"):
            validate_records([])

    def test_not_a_list_raises(self):
        with pytest.raises(PreprocessingError):
            validate_records(MINIMAL_RECORD)  # type: ignore

    def test_missing_single_field_raises(self):
        record = {k: v for k, v in MINIMAL_RECORD.items() if k != "duration"}
        with pytest.raises(PreprocessingError, match="duration"):
            validate_records([record])

    def test_missing_multiple_fields_raises(self):
        record = {k: v for k, v in MINIMAL_RECORD.items()
                  if k not in ("duration", "srcbytes", "flag")}
        with pytest.raises(PreprocessingError):
            validate_records([record])

    def test_non_dict_record_raises(self):
        with pytest.raises(PreprocessingError):
            validate_records(["not a dict"])

    def test_string_value_for_numeric_field_raises(self):
        record = {**MINIMAL_RECORD, "duration": "abc"}
        with pytest.raises(PreprocessingError, match="duration"):
            validate_records([record])

    def test_rate_above_1_raises(self):
        record = {**MINIMAL_RECORD, "serrorrate": 1.5}
        with pytest.raises(PreprocessingError, match="serrorrate"):
            validate_records([record])

    def test_rate_below_0_raises(self):
        record = {**MINIMAL_RECORD, "rerrorrate": -0.1}
        with pytest.raises(PreprocessingError, match="rerrorrate"):
            validate_records([record])

    def test_negative_srcbytes_raises(self):
        record = {**MINIMAL_RECORD, "srcbytes": -1}
        with pytest.raises(PreprocessingError, match="srcbytes"):
            validate_records([record])

    def test_invalid_protocoltype_raises(self):
        record = {**MINIMAL_RECORD, "protocoltype": "ftp"}
        with pytest.raises(PreprocessingError, match="protocoltype"):
            validate_records([record])

    def test_invalid_flag_raises(self):
        record = {**MINIMAL_RECORD, "flag": "BADVAL"}
        with pytest.raises(PreprocessingError, match="flag"):
            validate_records([record])

    def test_numeric_as_float_string_coerces(self):
        # "0.5" is a valid float string — should pass
        record = {**MINIMAL_RECORD, "serrorrate": "0.5"}
        validate_records([record])  # must not raise

    def test_rate_boundary_values_pass(self):
        record = {**MINIMAL_RECORD, "serrorrate": 0.0, "samesrvrate": 1.0}
        validate_records([record])

    def test_multiple_records_first_error_reported(self):
        bad1 = {k: v for k, v in MINIMAL_RECORD.items() if k != "duration"}
        bad2 = {**MINIMAL_RECORD, "srcbytes": -5}
        with pytest.raises(PreprocessingError):
            validate_records([bad1, bad2])


# ---------------------------------------------------------------------------
# engineer_features
# ---------------------------------------------------------------------------

class TestEngineerFeatures:

    def _df(self, record=None):
        return pd.DataFrame([record or MINIMAL_RECORD])

    def test_adds_is_s0_flag_true(self):
        df = self._df({**MINIMAL_RECORD, "flag": "S0"})
        result = engineer_features(df)
        assert result["is_s0_flag"].iloc[0] == 1

    def test_adds_is_s0_flag_false(self):
        df = self._df({**MINIMAL_RECORD, "flag": "SF"})
        result = engineer_features(df)
        assert result["is_s0_flag"].iloc[0] == 0

    def test_adds_is_icmp_true(self):
        df = self._df({**MINIMAL_RECORD, "protocoltype": "icmp"})
        result = engineer_features(df)
        assert result["is_icmp"].iloc[0] == 1

    def test_adds_is_icmp_false(self):
        df = self._df()
        result = engineer_features(df)
        assert result["is_icmp"].iloc[0] == 0

    def test_is_zero_byte_conn_true(self):
        df = self._df({**MINIMAL_RECORD, "srcbytes": 0, "dstbytes": 0})
        result = engineer_features(df)
        assert result["is_zero_byte_conn"].iloc[0] == 1

    def test_is_zero_byte_conn_false_when_srcbytes_nonzero(self):
        df = self._df({**MINIMAL_RECORD, "srcbytes": 1, "dstbytes": 0})
        result = engineer_features(df)
        assert result["is_zero_byte_conn"].iloc[0] == 0

    def test_original_df_not_mutated(self):
        df = self._df()
        original_cols = set(df.columns)
        engineer_features(df)
        assert set(df.columns) == original_cols

    def test_neptune_gets_correct_flags(self):
        df = pd.DataFrame([NEPTUNE_RECORD])
        result = engineer_features(df)
        assert result["is_s0_flag"].iloc[0] == 1
        assert result["is_icmp"].iloc[0] == 0
        assert result["is_zero_byte_conn"].iloc[0] == 1


# ---------------------------------------------------------------------------
# encode_service
# ---------------------------------------------------------------------------

class TestEncodeService:

    FREQ_MAP = {"http": 0.4, "ftp": 0.1, "private": 0.05}
    FALLBACK = 0.001

    def test_known_service_gets_freq(self):
        df = pd.DataFrame([{**MINIMAL_RECORD}])
        result = encode_service(df, self.FREQ_MAP, self.FALLBACK)
        assert abs(result["service_freq"].iloc[0] - 0.4) < 1e-9

    def test_unknown_service_gets_fallback(self):
        df = pd.DataFrame([{**MINIMAL_RECORD, "service": "unknown_svc"}])
        result = encode_service(df, self.FREQ_MAP, self.FALLBACK)
        assert abs(result["service_freq"].iloc[0] - self.FALLBACK) < 1e-9

    def test_service_column_dropped(self):
        df = pd.DataFrame([MINIMAL_RECORD])
        result = encode_service(df, self.FREQ_MAP, self.FALLBACK)
        assert "service" not in result.columns

    def test_service_freq_column_added(self):
        df = pd.DataFrame([MINIMAL_RECORD])
        result = encode_service(df, self.FREQ_MAP, self.FALLBACK)
        assert "service_freq" in result.columns

    def test_dict_freq_map(self):
        df = pd.DataFrame([{**MINIMAL_RECORD, "service": "ftp"}])
        result = encode_service(df, self.FREQ_MAP, self.FALLBACK)
        assert abs(result["service_freq"].iloc[0] - 0.1) < 1e-9
