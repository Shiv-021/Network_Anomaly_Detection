"""
config/columns.py
==================
Single source of truth for all NSL-KDD feature column definitions.

Every module that references feature names — training pipeline, inference
preprocessor, API routes — imports from here.  Never define them locally.
"""

# 37 raw numeric features (model was trained on exactly these)
NUMERIC_FEATURES: list[str] = [
    "duration", "srcbytes", "dstbytes", "land", "wrongfragment", "urgent", "hot",
    "numfailedlogins", "loggedin", "numcompromised", "rootshell", "suattempted",
    "numroot", "numfilecreations", "numshells", "numaccessfiles", "ishostlogin",
    "isguestlogin", "count", "srvcount", "serrorrate", "srvserrorrate", "rerrorrate",
    "srvrerrorrate", "samesrvrate", "diffsrvrate", "srvdiffhostrate", "dsthostcount",
    "dsthostsrvcount", "dsthostsamesrvrate", "dsthostdiffsrvrate",
    "dsthostsamesrcportrate", "dsthostsrvdiffhostrate", "dsthostserrorrate",
    "dsthostsrvserrorrate", "dsthostrerrorrate", "dsthostsrvrerrorrate",
]

# Categorical columns one-hot encoded during training (pd.get_dummies, drop_first=True)
CATEGORICAL_COLS: list[str] = ["protocoltype", "flag"]

# service is frequency-encoded (not one-hot) — kept separate
SERVICE_COL: str = "service"

# 3 binary features derived during both training and inference
ENGINEERED_FEATURES: list[str] = ["is_s0_flag", "is_icmp", "is_zero_byte_conn"]

# Target columns — present in training data, never in API requests
TARGET_COLS: list[str] = ["is_anomaly", "attack"]

# All raw fields a well-formed API request must include
REQUIRED_FIELDS: list[str] = NUMERIC_FEATURES + CATEGORICAL_COLS + [SERVICE_COL]

# Ordered column list for feature selection in the training pipeline
# (selector.py passes df_model with these columns → trainer → feature_columns.pkl)
MODELING_INPUT_COLS: list[str] = (
    ["protocoltype", "service", "flag"] + NUMERIC_FEATURES + ENGINEERED_FEATURES
)
