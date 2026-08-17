import { useEffect, useRef } from 'react'
import styles from './TrainLog.module.css'

const LINE_COLOR = {
  error: '#fca5a5',
  warn:  '#fcd34d',
  success: '#6ee7b7',
}

function colorLine(line) {
  const l = line.toLowerCase()
  if (l.includes('error') || l.includes('exception') || l.includes('failed')) return LINE_COLOR.error
  if (l.includes('warn') || l.includes('missing')) return LINE_COLOR.warn
  if (l.includes('complete') || l.includes('done') || l.includes('saved') || l.includes('loaded')) return LINE_COLOR.success
  return null
}

export default function TrainLog({ logLines, status, onStart, onReset, canStart, logFile }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines])

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📋 Training Progress</span>
        <div style={{ display: 'flex', gap: '.45rem' }}>
          {status !== 'idle' && (
            <button className="btn-icon" onClick={onReset}>↩ Reset</button>
          )}
          <button
            className="btn-primary"
            style={{ padding: '.45rem 1rem', fontSize: '.8rem' }}
            onClick={onStart}
            disabled={!canStart || status === 'running'}
          >
            {status === 'running' ? '⏳ Training…' : '🚀 Start Training'}
          </button>
        </div>
      </div>
      <div className={styles.log}>
        {logLines.length === 0 ? (
          <span className={styles.placeholder}>
            {status === 'idle'
              ? 'Select a dataset and click Start Training to begin.'
              : 'Waiting for log output…'}
          </span>
        ) : logLines.map((line, i) => {
          const color = colorLine(line)
          return (
            <div key={i} className={styles.line} style={color ? { color } : undefined}>
              {line}
            </div>
          )
        })}
        {status === 'done' && (
          <div className={styles.line} style={{ color: '#6ee7b7', fontWeight: 600 }}>
            ✅ Training complete!
          </div>
        )}
        {status === 'error' && (
          <div className={styles.line} style={{ color: '#fca5a5', fontWeight: 600 }}>
            ❌ Training failed. See errors above.
          </div>
        )}
        {logFile && (status === 'done' || status === 'error') && (
          <div className={styles.line} style={{ color: 'var(--text3)', fontSize: '.75rem', marginTop: '.4rem' }}>
            📁 Full verbose log → <code style={{ color: 'var(--text2)' }}>{logFile}</code>
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  )
}
