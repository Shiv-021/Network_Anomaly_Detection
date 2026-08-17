"""
backend/training/trainer/unsupervised.py
==========================================
Step 8 — Unsupervised anomaly detection methods.

CLUSTERING methods live here:
  K-Means (with/without QuantileTransformer — comparison)
  DBSCAN  (automatic eps via k-distance plot)
  Hierarchical / Agglomerative clustering + dendrogram

DIMENSIONALITY REDUCTION (PCA projection, t-SNE, PCA reconstruction
error) has its own module — see dimensionality_reduction.py. Clustering
groups points together; dimensionality reduction compresses the feature
space instead — they answer different questions, so they're kept in
separate files rather than one grab-bag "unsupervised" script. This
module calls into dimensionality_reduction.py at the right point (t-SNE
needs the K-Means/Hierarchical labels computed below) and folds all of
it into one comparison table for the dashboard.

Writes to state:
  pca_recon, recon_auc, recon_threshold   (via dimensionality_reduction.py)
"""
import json
import os
import warnings

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import QuantileTransformer
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score, davies_bouldin_score
from scipy.cluster.hierarchy import dendrogram, linkage as scipy_linkage

from .state import TrainingState
from .dimensionality_reduction import (
    run_pca_projection, run_tsne_projection, run_pca_reconstruction,
)

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
RANDOM_STATE = 42


def train_unsupervised(state: TrainingState) -> None:
    print("\n" + "#" * 70)
    print("# UNSUPERVISED METHODS")
    print("#" * 70)

    print("\nDiagnostic — columns with near-zero IQR:")
    q1 = state.X_train.astype(float).quantile(0.25)
    q3 = state.X_train.astype(float).quantile(0.75)
    zero_iqr = ((q3 - q1) < 1e-9).index[(q3 - q1) < 1e-9].tolist()
    print(f"  {zero_iqr}")

    qt       = QuantileTransformer(output_distribution="uniform",
                                    n_quantiles=1000, random_state=RANDOM_STATE)
    X_robust = qt.fit_transform(state.X_train.astype(float))

    SAMPLE_SIZE = 10_000
    rng = np.random.RandomState(RANDOM_STATE)
    idx = rng.choice(state.X_train.shape[0],
                      size=min(SAMPLE_SIZE, state.X_train.shape[0]), replace=False)
    X_samp   = X_robust[idx]
    y_samp   = state.y_train.values[idx]
    X_samp_s = state.X_train_scaled[idx]

    # PCA 2D projection — dimensionality reduction, not clustering.
    # See dimensionality_reduction.py for what this is and why it's separate.
    run_pca_projection(state, X_samp, y_samp)

    # K-Means
    print("\n--- K-Means: effect of QuantileTransformer ---")
    km_before = KMeans(n_clusters=2, random_state=RANDOM_STATE, n_init=10)
    lb_before = km_before.fit_predict(X_samp_s)
    match_b   = max((lb_before == y_samp).mean(), (lb_before == (1 - y_samp)).mean())
    print(f"BEFORE (StandardScaler):     Sil={silhouette_score(X_samp_s, lb_before):.4f}  "
          f"alignment={match_b:.4f}")

    km        = KMeans(n_clusters=2, random_state=RANDOM_STATE, n_init=10)
    km_labels = km.fit_predict(X_samp)
    match_a   = max((km_labels == y_samp).mean(), (km_labels == (1 - y_samp)).mean())
    km_sil    = float(silhouette_score(X_samp, km_labels))
    km_db     = float(davies_bouldin_score(X_samp, km_labels))
    print(f"AFTER  (QuantileTransformer): Sil={km_sil:.4f}  DB={km_db:.4f}  alignment={match_a:.4f}")

    # DBSCAN with auto eps
    MIN_SAMPLES = 10
    nn = NearestNeighbors(n_neighbors=MIN_SAMPLES)
    nn.fit(X_samp)
    k_dist, _ = nn.kneighbors(X_samp)
    auto_eps  = float(np.percentile(np.sort(k_dist[:, -1]), 90))
    print(f"\nDBSCAN auto eps (90th pct): {auto_eps:.4f}")
    plt.figure(figsize=(8, 5))
    plt.plot(np.sort(k_dist[:, -1]))
    plt.axhline(auto_eps, color="red", linestyle="--", label=f"eps={auto_eps:.4f}")
    plt.xlabel("Points sorted by k-distance")
    plt.ylabel(f"{MIN_SAMPLES}-NN distance")
    plt.title("DBSCAN k-distance plot")
    plt.legend()
    plt.tight_layout()
    state.savefig("dbscan_kdistance.png")

    dbscan    = DBSCAN(eps=auto_eps, min_samples=MIN_SAMPLES, n_jobs=-1)
    db_labels = dbscan.fit_predict(X_samp)
    n_clusters = len(set(db_labels)) - (1 if -1 in db_labels else 0)
    n_noise    = int((db_labels == -1).sum())
    print(f"DBSCAN — clusters: {n_clusters}, noise: {n_noise}")
    dbscan_sil = None
    dbscan_db  = None
    if n_clusters >= 2:
        nm = db_labels != -1
        dbscan_sil = float(silhouette_score(X_samp[nm], db_labels[nm]))
        dbscan_db  = float(davies_bouldin_score(X_samp[nm], db_labels[nm]))
        print(f"DBSCAN Sil={dbscan_sil:.4f}  DB={dbscan_db:.4f}")

    # Hierarchical clustering
    print("\nRunning Hierarchical (Agglomerative) Clustering…")
    hier        = AgglomerativeClustering(n_clusters=2, linkage="ward")
    hier_labels = hier.fit_predict(X_samp)
    match_h     = max((hier_labels == y_samp).mean(), (hier_labels == (1 - y_samp)).mean())
    hier_sil    = float(silhouette_score(X_samp, hier_labels))
    hier_db     = float(davies_bouldin_score(X_samp, hier_labels))
    print(f"Hierarchical: Sil={hier_sil:.4f}  DB={hier_db:.4f}  alignment={match_h:.4f}")

    dendro_idx = rng.choice(X_samp.shape[0], size=300, replace=False)
    Z = scipy_linkage(X_samp[dendro_idx], method="ward")
    plt.figure(figsize=(14, 6))
    dendrogram(Z, no_labels=True)
    plt.title("Hierarchical Clustering Dendrogram (300-point subsample)")
    plt.xlabel("Samples"); plt.ylabel("Distance")
    plt.tight_layout()
    state.savefig("dendrogram.png")

    # t-SNE — dimensionality reduction, not clustering. Reuses the cluster
    # labels computed above purely to color the visualization.
    run_tsne_projection(state, X_samp, y_samp, km_labels, hier_labels)

    # PCA Reconstruction Error — dimensionality reduction used as an
    # unsupervised anomaly score; this IS served at inference.
    run_pca_reconstruction(state)

    # ------------------------------------------------------------------
    # Save unsupervised comparison JSON for the dashboard
    # Metrics: Silhouette (higher better, -1..1), Davies-Bouldin (lower better, >=0)
    # For PCA: ROC-AUC is the quality metric.
    # ------------------------------------------------------------------
    unsu_rows = [
        {
            "Model":          "K-Means (QuantileTransformer)",
            "Silhouette":     round(km_sil, 4),
            "Davies-Bouldin": round(km_db, 4),
            "Note":           f"alignment={match_a:.3f} ({len(y_samp):,}-pt sample)",
        },
        {
            "Model":          "Hierarchical (Ward linkage)",
            "Silhouette":     round(hier_sil, 4),
            "Davies-Bouldin": round(hier_db, 4),
            "Note":           f"alignment={match_h:.3f} ({len(y_samp):,}-pt sample)",
        },
        {
            "Model":          "DBSCAN (auto eps)",
            "Silhouette":     round(dbscan_sil, 4) if dbscan_sil is not None else "—",
            "Davies-Bouldin": round(dbscan_db, 4)  if dbscan_db  is not None else "—",
            "Note":           f"{n_clusters} cluster(s), {n_noise} noise pts, eps={auto_eps:.4f}",
        },
        {
            "Model":          "PCA Reconstruction Error",
            "Silhouette":     "—",
            "Davies-Bouldin": "—",
            "ROC-AUC":        round(state.recon_auc, 4),
            "Note":           (f"Dimensionality reduction (15 PCA components) — reconstructs each "
                               f"connection and flags it anomalous above threshold={state.recon_threshold:.4f}"),
        },
    ]
    # Best = highest Silhouette among methods that have one
    sil_rows   = [r for r in unsu_rows if isinstance(r.get("Silhouette"), float)]
    best_unsup = max(sil_rows, key=lambda r: r["Silhouette"])["Model"] if sil_rows else "PCA Reconstruction Error"
    unsu_comp  = {"best": best_unsup, "models": unsu_rows}
    comp_path  = os.path.join(state.model_dir, "unsupervised_comparison.json")
    with open(comp_path, "w") as _f:
        json.dump(unsu_comp, _f, indent=2)
    print(f"  Saved: unsupervised_comparison.json")
