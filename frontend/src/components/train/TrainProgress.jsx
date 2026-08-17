import styles from './TrainProgress.module.css'

const STATUS_COLOR = {
  idle:    'var(--text3)',
  active:  'var(--accent)',
  done:    'var(--success)',
  error:   'var(--danger)',
}

export default function TrainProgress({ stepLabels, activeStep, status, noPlots, onTogglePlots }) {
  // activeStep: 0 (none) | 1-4

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">⚙️ Pipeline Options</span>
      </div>
      <div className="card-body">
        <label className={styles.toggle}>
          <input
            type="checkbox"
            checked={noPlots}
            onChange={e => onTogglePlots(e.target.checked)}
            disabled={status === 'running'}
          />
          <span className={styles.toggleLabel}>Skip plot generation (faster training)</span>
        </label>

        <div className={styles.steps}>
          {stepLabels.map((label, i) => {
            const n = i + 1
            let state = 'idle'
            if (status === 'running') {
              if (n < activeStep) state = 'done'
              else if (n === activeStep) state = 'active'
            } else if (status === 'done') {
              state = 'done'
            } else if (status === 'error' && n === activeStep) {
              state = 'error'
            }

            return (
              <div key={n} className={`${styles.step} ${styles[state]}`}>
                <div className={styles.stepNum} style={{ borderColor: STATUS_COLOR[state], color: STATUS_COLOR[state] }}>
                  {state === 'done' ? '✓' : state === 'error' ? '✕' : n}
                </div>
                <div>
                  <div className={styles.stepLabel}>{label}</div>
                  <div className={styles.stepState}>{state === 'active' ? 'Running…' : state === 'done' ? 'Complete' : state === 'error' ? 'Failed' : 'Waiting'}</div>
                </div>
                {state === 'active' && <div className={styles.pulse} />}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
