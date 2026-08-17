import { useRef, useState } from 'react'
import styles from './DataSource.module.css'

export default function DataSource({ dataInfo, onUpload, onUseLocal, disabled }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState(null)

  const handle = async (file) => {
    if (!file) return
    if (!file.name.endsWith('.csv')) { setError('Only .csv files are accepted.'); return }
    setError(null)
    try { await onUpload(file) }
    catch (e) { setError(e.message) }
  }

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    handle(file)
  }

  const onLocal = async () => {
    setError(null)
    try { await onUseLocal() }
    catch (e) { setError(e.message) }
  }

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">📂 Data Source</span></div>
      <div className="card-body">
        <div
          className={`${styles.drop} ${dragging ? styles.over : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !disabled && inputRef.current?.click()}
        >
          <span className={styles.dropIcon}>📁</span>
          <span className={styles.dropText}>
            {dragging ? 'Drop CSV here' : 'Drag & drop a CSV file, or click to browse'}
          </span>
          <span className={styles.dropSub}>NSL-KDD format · up to 200 MB</span>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            hidden
            onChange={e => handle(e.target.files[0])}
          />
        </div>

        <div className={styles.or}>or</div>

        <button
          className="btn-secondary"
          style={{ width: '100%' }}
          disabled={disabled}
          onClick={onLocal}
        >
          📊 Use bundled dataset (Network_anomaly_data.csv)
        </button>

        {error && <div className={styles.error}>{error}</div>}

        {dataInfo && (
          <div className={styles.info}>
            <span className={styles.infoIcon}>✅</span>
            <span><strong>{dataInfo.name}</strong> · {dataInfo.mb} MB loaded</span>
          </div>
        )}
      </div>
    </div>
  )
}
