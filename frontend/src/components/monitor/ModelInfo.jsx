import { useEffect } from 'react'
import useModelInfo from '../../hooks/useModelInfo'
import styles from './ModelInfo.module.css'

export default function ModelInfo({ modelsReady }) {
  const { info, loading, error, refresh } = useModelInfo()

  useEffect(() => { if (modelsReady) refresh() }, [modelsReady, refresh])

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🤖 Model Info</span>
        <button className="btn-icon" onClick={refresh}>↻</button>
      </div>
      <div className="card-body">
        {loading && <div className="empty-state">Loading…</div>}
        {error && <div className="empty-state" style={{ color: '#fca5a5' }}>{error}</div>}
        {info && (
          <>
            <ul className="info-list">
              <li><span className="info-key">Binary Model</span><span className="info-val">{info.binary_model || '–'}</span></li>
              <li><span className="info-key">Multiclass</span><span className="info-val">{info.multiclass_model || '–'}</span></li>
              <li><span className="info-key">Features</span><span className="info-val">{info.feature_count ?? '–'}</span></li>
              <li><span className="info-key">PCA Components</span><span className="info-val">{info.pca_components ?? '–'}</span></li>
              {info.decision_thresholds && Object.entries(info.decision_thresholds).map(([k, v]) => (
                <li key={k}>
                  <span className="info-key">{k.replace(/_/g, ' ')}</span>
                  <span className="info-val">{typeof v === 'number' ? v.toFixed(4) : v}</span>
                </li>
              ))}
            </ul>
            {info.supported_classes && (
              <div className="tag-wrap" style={{ marginTop: '.75rem' }}>
                {info.supported_classes.map(c => <span key={c} className="tag">{c}</span>)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
