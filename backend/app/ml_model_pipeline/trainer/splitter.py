"""
backend/training/trainer/splitter.py
=======================================
Step 1 — One-hot encode categorical columns, train/test split, scale.

Writes to state:
  X_train, X_test, X_train_raw, X_test_raw
  y_train, y_test, attack_train, attack_test
  X_train_scaled, X_test_scaled
  scaler, service_freq_map, fallback_freq, scale_pos_weight
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .state import TrainingState

RANDOM_STATE = 42


def prepare_splits(state: TrainingState) -> None:
    print("\n" + "=" * 70)
    print("STEP 1: DATA ENCODING, SPLIT, SCALING")
    print("=" * 70)

    df_enc = pd.get_dummies(state.df_model.copy(),
                            columns=["protocoltype", "flag"], drop_first=True)
    print(f"Shape after one-hot encoding: {df_enc.shape}")

    X_raw         = df_enc.drop(columns=["is_anomaly", "attack"])
    y_binary      = df_enc["is_anomaly"]
    attack_labels = df_enc["attack"]

    (state.X_train_raw, state.X_test_raw,
     state.y_train, state.y_test,
     state.attack_train, state.attack_test) = train_test_split(
        X_raw, y_binary, attack_labels,
        test_size=0.2, stratify=y_binary, random_state=RANDOM_STATE,
    )

    # Frequency-encode service on TRAIN only (no leakage)
    state.service_freq_map = state.X_train_raw["service"].value_counts(normalize=True)
    state.fallback_freq    = state.service_freq_map.min()

    state.X_train = state.X_train_raw.copy()
    state.X_test  = state.X_test_raw.copy()
    state.X_train["service_freq"] = state.X_train["service"].map(state.service_freq_map)
    state.X_test["service_freq"]  = (
        state.X_test["service"].map(state.service_freq_map).fillna(state.fallback_freq)
    )
    state.X_train = state.X_train.drop(columns=["service"])
    state.X_test  = state.X_test.drop(columns=["service"])
    print(f"Train shape: {state.X_train.shape}, Test shape: {state.X_test.shape}")

    state.scaler = StandardScaler()
    state.X_train_scaled = state.scaler.fit_transform(state.X_train)
    state.X_test_scaled  = state.scaler.transform(state.X_test)
    state.scale_pos_weight = (
        (state.y_train == 0).sum() / (state.y_train == 1).sum()
    )
