import ComparisonTable from '../ComparisonTable'

// Renders ONLY the model-comparison metrics tables. Deliberately does not
// include the Plots Gallery — that card is rendered separately in TrainTab
// so a failure to load/parse these metrics (e.g. a malformed comparison
// JSON) can never hide the plots too. See TrainTab.jsx.
export default function TrainResults({ results }) {
  if (!results) return null

  return (
    <div className="card" style={{ marginBottom: '1.2rem' }}>
      <div className="card-header">
        <span className="card-title">🏆 Model Comparison</span>
      </div>
      <div className="card-body">
        {results.binary && (
          <ComparisonTable title="Binary Classification (held-out test set)" data={results.binary} />
        )}
        {results.multiclass && (
          <ComparisonTable title="Multi-class Classification (held-out test set)" data={results.multiclass} />
        )}
        {results.cv && (
          <>
            <ComparisonTable title="Cross-Validation — Stratified 5-Fold" data={results.cv} />
            <div style={{ fontSize: '.68rem', color: 'var(--text3)', marginTop: '.4rem', lineHeight: 1.6 }}>
              CV F1 / CV ROC-AUC — mean across 5 folds on training data &nbsp;·&nbsp;
              Std — fold-to-fold variance (lower = more stable model)
            </div>
          </>
        )}
        {results.unsupervised && (
          <>
            <ComparisonTable title="Unsupervised Methods" data={results.unsupervised} />
            <div style={{ fontSize: '.68rem', color: 'var(--text3)', marginTop: '.4rem', lineHeight: 1.6 }}>
              Silhouette: −1→1 (cluster separation), higher is better &nbsp;·&nbsp;
              Davies-Bouldin: ≥0 (cluster compactness), lower is better &nbsp;·&nbsp;
              <strong>PCA Reconstruction Error</strong> is a <em>dimensionality-reduction</em> technique, not a
              cluster method — it compresses each connection to fewer dimensions then reconstructs it; a
              large reconstruction error means the traffic didn't fit the "normal" pattern learned by the
              compression, flagging it as anomalous. Its ROC-AUC column measures how well that error score
              separates normal vs. anomalous traffic.
            </div>
          </>
        )}
        {!results.binary && !results.multiclass && !results.unsupervised && !results.cv && (
          <div className="empty-state">Comparison data not available.</div>
        )}
      </div>
    </div>
  )
}
