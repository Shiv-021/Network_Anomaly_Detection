"""
backend/training/trainer/state.py
===================================
Shared mutable context container for the Trainer pipeline.

All step functions accept a TrainingState instance, read what they need,
and write their outputs back.  This avoids passing a growing argument list
between unrelated steps while keeping each module independently testable.
"""
import os


class TrainingState:
    """Mutable training context passed between pipeline step functions."""

    def __init__(self, df_model, model_dir: str, save_plots: bool, plot_dir: str):
        self.df_model   = df_model
        self.model_dir  = model_dir
        self.save_plots = save_plots
        self.plot_dir   = plot_dir

        # ----------------------------------------------------------------
        # splitter.prepare_splits output
        # ----------------------------------------------------------------
        self.X_train        = None
        self.X_test         = None
        self.X_train_raw    = None
        self.X_test_raw     = None
        self.y_train        = None
        self.y_test         = None
        self.attack_train   = None
        self.attack_test    = None
        self.X_train_scaled = None
        self.X_test_scaled  = None
        self.scaler         = None
        self.service_freq_map = None
        self.fallback_freq  = None
        self.scale_pos_weight = None

        # ----------------------------------------------------------------
        # binary_models.train_binary output
        # ----------------------------------------------------------------
        self.binary_models: dict = {}
        self.binary_preds:  dict = {}
        self.binary_probas: dict = {}
        self.xgb_model      = None

        # ----------------------------------------------------------------
        # threshold.tune_threshold output
        # ----------------------------------------------------------------
        self.chosen_threshold    = 0.5
        self.y_pred_recall_tuned = None

        # ----------------------------------------------------------------
        # binary_summary.summarize_binary output
        # ----------------------------------------------------------------
        self.results_df = None

        # ----------------------------------------------------------------
        # multiclass.train_multiclass output
        # ----------------------------------------------------------------
        self.le_attack       = None
        self.xgb_multi       = None
        self.best_multi_name = None

        # ----------------------------------------------------------------
        # unsupervised.train_unsupervised output
        # ----------------------------------------------------------------
        self.pca_recon       = None
        self.recon_auc       = None
        self.recon_threshold = None

    def savefig(self, name: str) -> None:
        """Save the current matplotlib figure to plot_dir and close it.

        Writes to a temp file first, then atomically renames it into place
        (os.replace). matplotlib's savefig() is NOT atomic — it writes bytes
        to the destination incrementally before closing — and every training
        run regenerates the exact same 21 filenames in plot_dir. Without
        this, a concurrent request for one of these files (e.g. the
        dashboard's Plots Gallery, viewed while a new training run is in
        progress) can read a half-written, corrupt PNG mid-save. os.replace()
        on the same filesystem is atomic, so a reader only ever sees the
        complete old file or the complete new one, never a partial write.
        """
        import matplotlib.pyplot as _plt
        if self.save_plots:
            final_path = os.path.join(self.plot_dir, name)
            tmp_path = os.path.join(self.plot_dir, f".{name}.tmp")
            # format="png" explicitly -- matplotlib otherwise infers the
            # output format from the filename's extension, and ".tmp" isn't
            # a format it recognizes (every name passed here is a .png).
            _plt.savefig(tmp_path, dpi=100, bbox_inches="tight", format="png")
            os.replace(tmp_path, final_path)
        _plt.close()
