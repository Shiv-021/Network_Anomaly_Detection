import { useState } from 'react'
import styles from './RawResponse.module.css'

export default function RawResponse({ raw }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    if (!raw) return
    await navigator.clipboard.writeText(raw).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📄 Raw Response</span>
        <button className="btn-icon" onClick={copy} disabled={!raw}>
          {copied ? '✓ Copied' : '⎘ Copy'}
        </button>
      </div>
      <div className="card-body" style={{ padding: 0 }}>
        {raw ? (
          <pre className={styles.pre}>{raw}</pre>
        ) : (
          <div className="empty-state">Raw JSON will appear here after a prediction.</div>
        )}
      </div>
    </div>
  )
}
