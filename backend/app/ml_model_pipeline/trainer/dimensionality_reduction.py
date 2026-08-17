"""
backend/app/ml_model_pipeline/trainer/dimensionality_reduction.py
====================================================================
Step 8a — Dimensionality-reduction techniques (PCA, t-SNE).

These are split out from unsupervised.py deliberately: PCA and t-SNE are
NOT clustering algorithms — they don't group points into clusters, they
compress the 40+ engineered features down to a handful of components.
K-Means / DBSCAN / Hierarchical clustering stay in unsupervised.py.

Two distinct uses of dimensionality reduction in this pipeline:

  1. VISUALIZATION ONLY — run_pca_projection() / run_tsne_projection()
     project the data down to 2D purely so a human can *see* whether
     normal vs. anomalous traffic separates visually. Nothing produced
     here is saved as a model or used at inference time.

  2. ANOMALY DETECTION (used at inference) — run_pca_reconstruction()
     fits a 15-component PCA on NORMAL traffic only, then measures how
     well any given connection can be reconstructed from that compressed
     representation. Normal traffic reconstructs well (low error);
     traffic that doesn't fit the learned "normal" pattern reconstructs
     poorly (high error) — that reconstruction error IS the anomaly
     score. This model is saved as pca_reconstruction_model.pkl and
     served at inference via backend/app/services/model_service.py.

When to use which
------------------
  - Need a quick 2D "does this even look separable?" sanity check → PCA
    projection (fast, linear, deterministic).
  - Need a sharper, non-linear 2D visualization for a report/demo → t-SNE
    (slower, better visual cluster separation, not deterministic/stable
    enough to use as a production feature).
  - Need an actual unsupervised anomaly score to serve at inference,
    with no labels required at prediction time → PCA reconstruction
    error (this is the one that ships).

Writes to state (consumed by binary_summary.py's comparison table and by
artifacts.py, which pickles state.pca_recon for serving):
  pca_recon, recon_auc, recon_threshold
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import roc_auc_score, classification_report

from .state import TrainingState

RANDOM_STATE = 42


def run_pca_projection(state: TrainingState, X_samp, y_samp) -> np.ndarray:
    """2D PCA scatter plot, colored by true label. Visualization only."""
    print("\n" + "=" * 70)
    print("DIMENSIONALITY REDUCTION: PCA Projection (2D, visualization only)")
    print("=" * 70)
    pca2  = PCA(n_components=2, random_state=RANDOM_STATE)
    X_pca = pca2.fit_transform(X_samp)
    print(f"PCA explained variance (2 components): "
          f"{pca2.explained_variance_ratio_.sum():.4f}")

    plt.figure(figsize=(8, 6))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y_samp, cmap="coolwarm", s=5, alpha=0.5)
    plt.title("PCA Projection (2D) — colored by true is_anomaly")
    plt.xlabel("PC1"); plt.ylabel("PC2")
    plt.colorbar(label="is_anomaly")
    plt.tight_layout()
    state.savefig("pca_projection.png")
    return X_pca


def run_tsne_projection(state: TrainingState, X_samp, y_samp, km_labels, hier_labels) -> np.ndarray:
    """
    2D t-SNE scatter plots (visualization only), one panel each for the
    true label and the two clustering results computed upstream in
    unsupervised.py (K-Means, Hierarchical) — lets you eyeball how well
    each clustering aligns with the non-linear t-SNE layout.
    """
    print("\n" + "=" * 70)
    print("DIMENSIONALITY REDUCTION: t-SNE Projection (2D, may take a minute)")
    print("=" * 70)
    tsne   = TSNE(n_components=2, random_state=RANDOM_STATE, perplexity=30, init="pca")
    X_tsne = tsne.fit_transform(X_samp)

    fig, axes = plt.subplots(1, 3, figsize=(22, 6))
    axes[0].scatter(X_tsne[:, 0], X_tsne[:, 1], c=y_samp,      cmap="coolwarm", s=5, alpha=0.5)
    axes[0].set_title("t-SNE — true is_anomaly")
    axes[1].scatter(X_tsne[:, 0], X_tsne[:, 1], c=km_labels,   cmap="viridis",  s=5, alpha=0.5)
    axes[1].set_title("t-SNE — K-Means cluster")
    axes[2].scatter(X_tsne[:, 0], X_tsne[:, 1], c=hier_labels, cmap="plasma",   s=5, alpha=0.5)
    axes[2].set_title("t-SNE — Hierarchical cluster")
    plt.tight_layout()
    state.savefig("tsne_comparison.png")
    return X_tsne


def run_pca_reconstruction(state: TrainingState) -> None:
    """
    Fit PCA on normal-only traffic and use reconstruction error as an
    unsupervised anomaly score. Unlike the two functions above, this
    result IS used at inference time (see model_service.py) and IS
    saved as an artifact (pca_reconstruction_model.pkl).

    Writes to state: pca_recon, recon_auc, recon_threshold
    """
    print("\n" + "=" * 70)
    print("DIMENSIONALITY REDUCTION: PCA Reconstruction Error (unsupervised anomaly score)")
    print("=" * 70)
    X_norm_sc = state.scaler.transform(state.X_train[state.y_train == 0])
    n_comp    = 15
    state.pca_recon = PCA(n_components=n_comp, random_state=RANDOM_STATE)
    state.pca_recon.fit(X_norm_sc)
    print(f"Explained variance ({n_comp} components): "
          f"{state.pca_recon.explained_variance_ratio_.sum():.4f}")

    X_recon   = state.pca_recon.inverse_transform(
        state.pca_recon.transform(state.X_test_scaled)
    )
    recon_err = np.mean((state.X_test_scaled - X_recon) ** 2, axis=1)
    state.recon_auc = roc_auc_score(state.y_test, recon_err)
    print(f"ROC-AUC (PCA reconstruction): {state.recon_auc:.4f}")

    X_nr     = state.pca_recon.inverse_transform(state.pca_recon.transform(X_norm_sc))
    norm_err = np.mean((X_norm_sc - X_nr) ** 2, axis=1)
    state.recon_threshold = float(np.percentile(norm_err, 95))
    y_pred_recon = (recon_err > state.recon_threshold).astype(int)
    print(f"\nAt 95th-pct normal threshold ({state.recon_threshold:.4f}):")
    print(classification_report(state.y_test, y_pred_recon, target_names=["Normal", "Anomaly"]))

    plt.figure(figsize=(8, 5))
    plt.hist(recon_err[state.y_test == 0], bins=50, alpha=0.6, label="Normal",  density=True)
    plt.hist(recon_err[state.y_test == 1], bins=50, alpha=0.6, label="Anomaly", density=True)
    plt.axvline(state.recon_threshold, color="black", linestyle="--",
                label="95th pct normal threshold")
    plt.xlabel("PCA Reconstruction Error"); plt.ylabel("Density")
    plt.title("PCA Reconstruction Error — Normal vs Anomaly")
    plt.legend()
    plt.xlim(0, np.percentile(recon_err, 99))
    plt.tight_layout()
    state.savefig("pca_reconstruction_error.png")
