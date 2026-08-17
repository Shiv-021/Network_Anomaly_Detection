"""
backend/training/eda/security_indicators.py
=============================================
Step 11 — Security-indicator features stratified by class label.

Produces a 3×3 grid (one panel per feature) where each panel shows:
  - % of records where the feature is > 0  (Normal vs Anomaly, top half)
  - Mean value per class                   (bar chart, bottom half)

Features visualised
-------------------
  wrongfragment, urgent, numfailedlogins,
  rootshell, suattempted, numshells,
  numaccessfiles, numroot, numcompromised
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

_SECURITY_FEATURES = [
    "wrongfragment",
    "urgent",
    "numfailedlogins",
    "rootshell",
    "suattempted",
    "numshells",
    "numaccessfiles",
    "numroot",
    "numcompromised",
]

_LABELS = {0: "Normal", 1: "Anomaly"}
_COLORS = {"Normal": "#4CAF50", "Anomaly": "#F44336"}


def plot(df: pd.DataFrame, savefig) -> None:
    """
    Save security_indicators.png — 3×3 grid of dual-bar panels.

    Requires 'is_anomaly' column to already exist (added by Step 1).
    Silently drops any feature not present in df.
    """
    features = [f for f in _SECURITY_FEATURES if f in df.columns]
    if not features or "is_anomaly" not in df.columns:
        return

    fig, axes = plt.subplots(3, 3, figsize=(16, 14))
    fig.suptitle(
        "Security Indicator Features — Normal vs Anomaly",
        fontsize=15,
        fontweight="bold",
        y=1.01,
    )

    groups = df.groupby("is_anomaly")

    for idx, feat in enumerate(features):
        ax = axes[idx // 3][idx % 3]

        pct_nonzero = {}
        mean_val = {}
        for label_int, label_str in _LABELS.items():
            grp = groups.get_group(label_int) if label_int in groups.groups else pd.DataFrame()
            if grp.empty:
                pct_nonzero[label_str] = 0.0
                mean_val[label_str] = 0.0
            else:
                pct_nonzero[label_str] = (grp[feat] > 0).mean() * 100
                mean_val[label_str] = grp[feat].mean()

        x = [0, 1]
        labels = list(_LABELS.values())
        colors = [_COLORS[l] for l in labels]

        # top half — % non-zero
        ax2 = ax.twinx()
        bars1 = ax.bar(
            [v - 0.18 for v in x],
            [pct_nonzero[l] for l in labels],
            width=0.32,
            color=colors,
            alpha=0.85,
            label="% non-zero",
        )
        # bottom half — mean value (secondary y)
        bars2 = ax2.bar(
            [v + 0.18 for v in x],
            [mean_val[l] for l in labels],
            width=0.32,
            color=colors,
            alpha=0.40,
            hatch="//",
            label="mean value",
        )

        ax.set_title(feat, fontsize=10, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("% records > 0", fontsize=8, color="#333")
        ax2.set_ylabel("mean value", fontsize=8, color="#888")
        ax2.tick_params(axis="y", labelcolor="#888", labelsize=7)

        # value labels on the % bars
        for bar in bars1:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.3,
                f"{h:.1f}%",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color="#222",
                clip_on=True,   # see note below -- required to avoid a savefig bug
            )

    # hide any unused axes (grid is always 3×3, features list may be < 9)
    for idx in range(len(features), 9):
        axes[idx // 3][idx % 3].set_visible(False)

    # subplots_adjust with explicit values, NOT tight_layout(): tight_layout()
    # doesn't reliably account for twinx() secondary axes across a 3x3 grid
    # and was silently failing here (a UserWarning, easy to miss in a wall of
    # training output). That combined with bbox_inches="tight" in savefig()
    # (shared by every plot in the pipeline) to compute a wildly oversized
    # bounding box -- this figure was being saved at ~1400x11300px instead of
    # the intended ~1600x1400, a ignore-at-a-glance-but-broken-on-open PNG.
    # The `clip_on=True` above on the value-label text is the other half of
    # the fix: without it, bbox_inches="tight" still blows up even with
    # subplots_adjust, because it also computes bounding boxes for text
    # artists and this specific combination (twinx + unclipped text) confuses
    # that calculation. Both were verified necessary and sufficient together.
    fig.subplots_adjust(left=0.06, right=0.94, top=0.93, bottom=0.05, hspace=0.55, wspace=0.35)
    savefig("security_indicators.png")
