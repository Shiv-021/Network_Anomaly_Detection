import Gauge from './Gauge'
import styles from './Verdict.module.css'

const EP_LABEL = {
  '/predict':                 'Binary Detection',
  '/predict/attack-type':     'Attack Type',
  '/predict/reconstruction':  'Reconstruction',
  '/predict/full':            'Full Analysis',
}

export default function Verdict({ result }) {
  if (!result) {
    return (
      <div className="card">
        <div className="card-header"><span className="card-title">📋 Analysis Result</span></div>
        <div className="card-body">
          <div className="empty-state">Run an analysis to see results here.</div>
        </div>
      </div>
    )
  }

  const isAnomaly = result.isAnomaly
  const mixed     = result.mixedSignal
  const badgeCls  = mixed ? 'badge badge-warn' : (isAnomaly ? 'badge badge-anomaly' : 'badge badge-normal')

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📋 Analysis Result</span>
        <span
          className={badgeCls}
          title={mixed ? 'Binary model says normal, but the attack-type model confidently named a specific attack — worth a second look.' : undefined}
        >
          {mixed ? '⚠️ MIXED SIGNAL' : (isAnomaly ? '🚨 ANOMALY' : '✅ NORMAL')}
        </span>
      </div>
      <div className="card-body">
        <div className={styles.layout}>
          <div className={styles.gaugeWrap}>
            <Gauge value={result.mainScore} />
            <div className={`${styles.verdict} ${mixed ? styles.mixed : (isAnomaly ? styles.anomaly : styles.normal)}`}>
              {mixed ? '🟡 CONFLICTING MODELS' : (isAnomaly ? '🔴 THREAT DETECTED' : '🟢 SAFE TRAFFIC')}
            </div>
            {mixed && (
              <div style={{ fontSize: '.7rem', color: 'var(--text3)', marginTop: '.4rem', lineHeight: 1.5, textAlign: 'center' }}>
                Binary model: normal ({(result.mainScore * 100).toFixed(1)}%) &nbsp;·&nbsp;
                Attack-type model: <strong>{result.attackClass}</strong> ({(result.attackConfidence * 100).toFixed(1)}%)
              </div>
            )}
          </div>
          <div className={styles.details}>
            <ul className="info-list">
              <li>
                <span className="info-key">Verdict</span>
                <span className="info-val">{result.mainLabel}</span>
              </li>
              {result.binary && (
                <li>
                  <span className="info-key">Anomaly Prob.</span>
                  <span className="info-val">{(result.binary.anomalyProb * 100).toFixed(2)}%</span>
                </li>
              )}
              {result.multiclass && (
                <li>
                  <span className="info-key">Attack Class</span>
                  <span className="info-val">{result.multiclass.class}</span>
                </li>
              )}
              {result.multiclass && (
                <li>
                  <span className="info-key">Confidence</span>
                  <span className="info-val">{(result.multiclass.confidence * 100).toFixed(2)}%</span>
                </li>
              )}
              {result.reconstruction && (
                <li>
                  <span className="info-key">Recon Error</span>
                  <span className="info-val">{result.reconstruction.error.toFixed(5)}</span>
                </li>
              )}
              <li>
                <span className="info-key">Mode</span>
                <span className="info-val">{EP_LABEL[result.endpoint] || result.endpoint}</span>
              </li>
            </ul>

            {result.topPredictions && (
              <div className={styles.topPreds}>
                <div className={styles.topTitle}>Top Predictions</div>
                {result.topPredictions.map(p => (
                  <div key={p.class} className={styles.topRow}>
                    <span className={styles.topClass}>{p.class}</span>
                    <div className={styles.topBar}>
                      <div
                        className={styles.topFill}
                        style={{ width: `${(p.probability * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className={styles.topPct}>{(p.probability * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
