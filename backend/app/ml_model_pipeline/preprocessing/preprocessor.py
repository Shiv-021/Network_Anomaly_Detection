"""
backend/core/preprocessor.py
==============================
Turns raw NSL-KDD-style connection records (as submitted to the API in JSON)
into the exact feature matrix the trained models expect.

This mirrors, step for step, the feature engineering done in Block 2 (EDA)
and Block 3 (ML Modeling) of the training pipeline:
  1. Engineered binary features: is_s0_flag, is_icmp, is_zero_byte_conn
  2. One-hot encoding of protocoltype and flag (drop_first=True, same as training)
  3. Frequency encoding of service (using the TRAIN-fit frequency map, with a
     fallback for services never seen during training)
  4. Reindexing to the exact column order/set the model was trained on
     (feature_columns.pkl) -- any column the model expects but this request
     didn't produce gets filled with 0; any extra column is dropped. This is
     what makes preprocessing robust to partial or reordered input.

If you retrain the model with a different feature set, you do NOT need to
edit this file -- it reads its column contract from feature_columns.pkl.
"""

import pandas as pd

from config.columns import NUMERIC_FEATURES, CATEGORICAL_COLS, SERVICE_COL, REQUIRED_FIELDS

# Valid categorical values seen during training
_VALID_PROTOCOL_TYPES = {"tcp", "udp", "icmp"}
_VALID_FLAGS = {"SF", "S0", "S1", "S2", "S3", "REJ", "RSTO", "RSTOS0",
                "RSTR", "SH", "OTH"}
# Rate features must be in [0, 1]; byte/count features must be non-negative
_RATE_FEATURES = {
    "serrorrate", "srvserrorrate", "rerrorrate", "srvrerrorrate",
    "samesrvrate", "diffsrvrate", "srvdiffhostrate",
    "dsthostsamesrvrate", "dsthostdiffsrvrate", "dsthostsamesrcportrate",
    "dsthostsrvdiffhostrate", "dsthostserrorrate", "dsthostsrvserrorrate",
    "dsthostrerrorrate", "dsthostsrvrerrorrate",
}
_NON_NEGATIVE = {"srcbytes", "dstbytes", "duration", "count", "srvcount",
                 "dsthostcount", "dsthostsrvcount"}


class PreprocessingError(ValueError):
    """Raised when a request can't be turned into a valid feature vector."""
    pass


def validate_records(records):
    """
    records: list of dicts (raw request payload, one dict per connection).
    Raises PreprocessingError listing every missing field, type error, and
    out-of-range value across every record.
    """
    if not isinstance(records, list) or len(records) == 0:
        raise PreprocessingError(
            "Expected a non-empty list of records under 'data' "
            "(a single record should still be wrapped in a list of length 1)."
        )

    problems = []
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            problems.append(f"record[{i}] is not a JSON object.")
            continue

        # Missing fields
        missing = [f for f in REQUIRED_FIELDS if f not in record]
        if missing:
            problems.append(f"record[{i}] missing fields: {missing}")
            continue  # can't validate values if fields are missing

        # Numeric fields must be numeric
        for col in NUMERIC_FEATURES:
            val = record[col]
            try:
                fval = float(val)
            except (TypeError, ValueError):
                problems.append(f"record[{i}].{col}: expected numeric, got {type(val).__name__!r} ({val!r})")
                continue
            # Rate features must be in [0, 1]
            if col in _RATE_FEATURES and not (0.0 <= fval <= 1.0):
                problems.append(f"record[{i}].{col}: rate feature must be in [0, 1], got {fval}")
            # Byte/count features must be non-negative
            if col in _NON_NEGATIVE and fval < 0:
                problems.append(f"record[{i}].{col}: must be >= 0, got {fval}")

        # Categorical: warn on unseen values (not hard error — freq encoding handles service)
        proto = record.get("protocoltype", "")
        if proto not in _VALID_PROTOCOL_TYPES:
            problems.append(
                f"record[{i}].protocoltype: unrecognised value {proto!r}. "
                f"Expected one of {sorted(_VALID_PROTOCOL_TYPES)}."
            )
        flag = record.get("flag", "")
        if flag not in _VALID_FLAGS:
            problems.append(
                f"record[{i}].flag: unrecognised value {flag!r}. "
                f"Expected one of {sorted(_VALID_FLAGS)}."
            )

    if problems:
        raise PreprocessingError("Invalid request payload: " + " | ".join(problems))


def engineer_features(df):
    """Adds the same 3 engineered binary features used in training."""
    df = df.copy()
    df['is_s0_flag'] = (df['flag'] == 'S0').astype(int)
    df['is_icmp'] = (df['protocoltype'] == 'icmp').astype(int)
    df['is_zero_byte_conn'] = (
        (df['srcbytes'].astype(float) == 0) & (df['dstbytes'].astype(float) == 0)
    ).astype(int)
    return df


def encode_service(df, service_freq_map, fallback_freq):
    """
    Frequency-encodes the service column using the TRAIN-fit map. Services
    never seen during training fall back to the lowest observed frequency
    (treated as "rare/unknown"), exactly as done in Block 3, Step 2.
    """
    df = df.copy()
    freq_map = service_freq_map if isinstance(service_freq_map, dict) else service_freq_map.to_dict()
    df['service_freq'] = df[SERVICE_COL].map(freq_map).fillna(fallback_freq)
    df = df.drop(columns=[SERVICE_COL])
    return df


def preprocess(records, artifacts):
    """
    Full pipeline: raw JSON records -> model-ready feature matrix.

    records: list of raw request dicts.
    artifacts: dict with keys 'service_freq_map', 'fallback_freq',
               'feature_columns' (loaded once at app startup -- see app.py).

    Returns: pandas DataFrame with exactly artifacts['feature_columns'] as
             columns, in that order, ready to hand to model.predict().
    """
    validate_records(records)

    df = pd.DataFrame(records)

    # Coerce numeric fields (JSON numbers sometimes arrive as strings from
    # certain clients/tools -- fail loudly and specifically if they're not
    # actually numeric rather than letting a silent NaN through).
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    bad_numeric = df[NUMERIC_FEATURES].isnull().any()
    if bad_numeric.any():
        bad_cols = bad_numeric[bad_numeric].index.tolist()
        raise PreprocessingError(
            f"Non-numeric or missing values found in numeric fields: {bad_cols}"
        )

    df = engineer_features(df)
    df = encode_service(df, artifacts['service_freq_map'], artifacts['fallback_freq'])
    df = pd.get_dummies(df, columns=CATEGORICAL_COLS, drop_first=True)

    # Reindex to the exact training-time column contract: any expected
    # column this batch didn't produce (e.g. protocoltype_udp never
    # appeared because every record in this batch was tcp) gets filled
    # with 0; anything extra (e.g. an unexpected flag value one-hot'd
    # into a column the model never saw) gets dropped. This is what makes
    # preprocessing robust to small/single-record requests.
    feature_columns = artifacts['feature_columns']
    df = df.reindex(columns=feature_columns, fill_value=0)

    return df
