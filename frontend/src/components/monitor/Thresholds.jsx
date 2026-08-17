import styles from './Thresholds.module.css'

export default function Thresholds({ result }) {
  const rows = []

  if (result?.binary) {
    const p = result.binary.anomalyProb ?? 0
    rows.push({ label: 'Anomaly Probability', value: p, pct: p * 100, color: p > 0.7 ? '#ef4444' : p > 0.4 ? '#f59e0b' : '#10b981' })
  }
  if (result?.multiclass) {
    const c = result.multiclass.confidence ?? 0
    rows.push({ label: 'Class Confidence', value: c, pct: c * 100, color: '#3b82f6' })
  }
  if (result?.reconstruction) {
    const e = result.reconstruction.error ?? 0
    const pct = Math.min(e * 1000, 100)
    rows.push({ label: 'Reconstruction Error', value: e, pct, color: e > 0.05 ? '#ef4444' : '#10b981', raw: e.toFixed(5) })
  }

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">📊 Score Breakdown</span></div>
      <div className="card-body">
        {rows.length === 0 ? (
          <div className="empty-state">Run a prediction to see scores.</div>
        ) : rows.map(r => (
          <div key={r.label} className={styles.row}>
            <div className={styles.meta}>
              <span className={styles.label}>{r.label}</span>
              <span className={styles.val} style={{ color: r.color }}>{r.raw ?? (r.value * 100).toFixed(1) + '%'}</span>
            </div>
            <div className={styles.track}>
              <div className={styles.fill} style={{ width: `${r.pct}%`, background: r.color }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
