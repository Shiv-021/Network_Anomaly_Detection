import styles from './HistoryTable.module.css'

const EP_SHORT = {
  '/predict':                 'Binary',
  '/predict/attack-type':     'Multiclass',
  '/predict/reconstruction':  'Recon',
  '/predict/full':            'Full',
}

export default function HistoryTable({ history, onClear }) {
  if (history.length === 0) {
    return (
      <div className="card">
        <div className="card-header"><span className="card-title">📜 Prediction History</span></div>
        <div className="card-body">
          <div className="empty-state">Predictions made in this session will appear here.</div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📜 Prediction History</span>
        <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center' }}>
          <span className="badge badge-warn">{history.length} records</span>
          <button className="btn-icon" onClick={onClear}>Clear</button>
        </div>
      </div>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>#</th>
              <th>Time</th>
              <th>Mode</th>
              <th>Verdict</th>
              <th>Score</th>
              <th>Attack Class</th>
            </tr>
          </thead>
          <tbody>
            {[...history].reverse().map((h, i) => (
              <tr key={i} className={h.isAnomaly ? styles.anomalyRow : ''}>
                <td>{history.length - i}</td>
                <td>{h.time}</td>
                <td>{EP_SHORT[h.endpoint] || h.endpoint}</td>
                <td>
                  {h.mixedSignal ? (
                    <span
                      className="badge badge-warn"
                      title="Binary model says normal, but the attack-type model confidently named a specific attack — worth a second look."
                    >
                      ⚠️ MIXED SIGNAL
                    </span>
                  ) : (
                    <span className={`badge ${h.isAnomaly ? 'badge-anomaly' : 'badge-normal'}`}>
                      {h.isAnomaly ? '🚨 ANOMALY' : '✅ NORMAL'}
                    </span>
                  )}
                </td>
                <td className={styles.score}>{(h.mainScore * 100).toFixed(1)}%</td>
                <td className={styles.cls}>{h.attackClass || '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
