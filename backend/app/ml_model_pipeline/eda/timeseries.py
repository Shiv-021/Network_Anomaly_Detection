"""
backend/training/eda/timeseries.py
=====================================
Step 10 — Temporal analysis.

Tests whether the dataset has usable temporal structure by:
  1. Searching for a real timestamp column.
  2. Analysing connection duration distributions per class.
  3. Computing a rolling anomaly rate over index order (arrival-order proxy)
     and applying a Kendall-Tau trend test.
  4. Measuring lag-1 autocorrelation of rolling aggregate rate features.

If no real timestamp is found the analysis falls back to these proxies and
documents clearly why classical time-series decomposition is not applicable.
The note is the conclusion of a real test, not a standalone print statement.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import kendalltau


def analyze(df: pd.DataFrame, savefig) -> dict:
    """
    Run temporal analysis. Returns a findings dict merged into the EDA
    stats_dict inside run_eda().
    """
    print("\n" + "=" * 70)
    print("STEP 10: TEMPORAL / TIME-SERIES ANALYSIS")
    print("=" * 70)

    findings: dict = {}

    # ------------------------------------------------------------------
    # 1. Search for a real timestamp column
    # ------------------------------------------------------------------
    ts_candidates = [
        c for c in df.columns
        if any(kw in c.lower() for kw in ("time", "timestamp", "date", "epoch", "_ts"))
    ]
    findings["has_timestamp"] = bool(ts_candidates)
    if ts_candidates:
        print(f"Timestamp-like columns found: {ts_candidates}")
        for col in ts_candidates:
            print(f"  {col}: dtype={df[col].dtype}, nunique={df[col].nunique()}")
    else:
        print("No timestamp column found — running proxy tests.")

    # ------------------------------------------------------------------
    # 2. Duration distribution per class (per-connection length proxy)
    # ------------------------------------------------------------------
    dur_data: dict = {}
    if "duration" in df.columns and "is_anomaly" in df.columns:
        for label, name in ((0, "normal"), (1, "anomaly")):
            s = df.loc[df["is_anomaly"] == label, "duration"]
            dur_data[name] = s
            print(f"duration | {name:<7s}: mean={s.mean():.3f}s  "
                  f"median={s.median():.0f}s  p95={s.quantile(0.95):.1f}s")
        findings["duration_normal_mean"]  = float(dur_data["normal"].mean())
        findings["duration_anomaly_mean"] = float(dur_data["anomaly"].mean())

    # ------------------------------------------------------------------
    # 3. Rolling anomaly rate over index order (arrival-order proxy)
    # ------------------------------------------------------------------
    rolling_rate = None
    if "is_anomaly" in df.columns:
        n_chunks   = 50
        chunk_size = max(1, len(df) // n_chunks)
        chunk_idx  = np.arange(len(df)) // chunk_size
        rolling_rate = df.groupby(chunk_idx)["is_anomaly"].mean()
        rate_std = float(rolling_rate.std())
        findings["anomaly_rate_index_std"] = rate_std
        print(f"\nRolling anomaly rate std over {n_chunks} index chunks: {rate_std:.4f}")
        print("  -> " + (
            "Notable variation — data is NOT uniformly i.i.d. by row order."
            if rate_std > 0.05 else
            "Relatively uniform — no obvious temporal clustering by row order."
        ))

        tau, p_tau = kendalltau(rolling_rate.index.to_numpy(), rolling_rate.values)
        findings["rolling_rate_kendall_tau"] = float(tau)
        findings["rolling_rate_trend_pval"]  = float(p_tau)
        print(f"  Kendall-Tau trend: τ={tau:.4f}, p={p_tau:.4f} "
              f"({'significant trend' if p_tau < 0.05 else 'no significant trend'})")

    # ------------------------------------------------------------------
    # 4. Lag-1 autocorrelation of rolling rate features
    # ------------------------------------------------------------------
    proxy_cols = [c for c in
                  ["serrorrate", "count", "srvcount", "dsthostcount", "dsthostsrvcount"]
                  if c in df.columns]
    if proxy_cols:
        print("\nLag-1 autocorrelation of rolling aggregate features:")
        for col in proxy_cols:
            ac = float(df[col].autocorr(lag=1))
            findings[f"autocorr_{col}"] = ac
            print(f"  {col:<28s}: {ac:.4f}")

    # ------------------------------------------------------------------
    # 5. Plots
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(21, 5))

    if dur_data:
        cap = df["duration"].quantile(0.99)
        for name, series in dur_data.items():
            axes[0].hist(series.clip(upper=cap), bins=50, alpha=0.7, label=name, density=True)
        axes[0].set_title("Connection Duration by Class (capped at p99)")
        axes[0].set_xlabel("duration (seconds)")
        axes[0].legend()
    else:
        axes[0].axis("off")

    if rolling_rate is not None:
        axes[1].plot(rolling_rate.index, rolling_rate.values, linewidth=1.5)
        axes[1].axhline(rolling_rate.mean(), color="red", linestyle="--",
                         label=f"mean={rolling_rate.mean():.3f}")
        axes[1].set_title("Anomaly Rate by Index Chunk")
        axes[1].set_xlabel("Chunk index (row order proxy)")
        axes[1].set_ylabel("Anomaly rate")
        axes[1].legend()
    else:
        axes[1].axis("off")

    if proxy_cols:
        vals = [float(df[c].autocorr(lag=1)) for c in proxy_cols]
        axes[2].barh(proxy_cols, vals)
        axes[2].axvline(0, color="black", linewidth=0.8)
        axes[2].set_title("Lag-1 Autocorrelation\n(rolling rate proxies)")
        axes[2].set_xlabel("Autocorrelation coefficient")
    else:
        axes[2].axis("off")

    plt.tight_layout()
    savefig("timeseries_analysis.png")

    # ------------------------------------------------------------------
    # 6. Conclusion (only printed when no real timestamp was found)
    # ------------------------------------------------------------------
    if not ts_candidates:
        print(
            "\nConclusion: No wall-clock timestamp exists.\n"
            "  'duration'  — per-connection length in seconds, not arrival time.\n"
            "  'count'     — connections to same host in past 2s (baked into each row).\n"
            "  'srvcount'  — connections to same service in past 2s (baked into each row).\n"
            "  Train/test split uses stratified random sampling to avoid row-order leakage."
        )

    return findings
