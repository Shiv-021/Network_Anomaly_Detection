import { useRef, useEffect } from 'react'
import Chart from 'chart.js/auto'
import styles from './LiveMonitor.module.css'

const MAX_POINTS = 40

export default function LiveMonitor({ points, liveRunning, onToggle, feed, modelsReady, visible }) {
  // points: [{prob, isAnomaly}]
  const canvasRef = useRef(null)
  const chartRef  = useRef(null)

  useEffect(() => {
    if (!canvasRef.current) return
    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          data: [],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,.07)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: [],
          pointBorderColor: [],
          pointBorderWidth: 1,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false }, tooltip: {
          callbacks: { label: ctx => ` Anomaly prob: ${(ctx.raw * 100).toFixed(1)}%` }
        }},
        scales: {
          x: { display: false },
          y: {
            min: 0, max: 1,
            grid: { color: 'rgba(30,58,95,.4)' },
            ticks: { color: '#64748b', font: { size: 10 }, callback: v => (v * 100) + '%' }
          }
        }
      }
    })
    return () => { chartRef.current?.destroy(); chartRef.current = null }
  }, [])

  // This tab is toggled with `display: none` rather than unmounted (so
  // Simulate keeps polling in the background while you're on the Train
  // tab). Chart.js's resize-observer doesn't reliably fire when a
  // display:none parent becomes visible again, so the canvas can render
  // stretched/distorted until something forces a resize. Force one
  // explicitly whenever this tab becomes visible again.
  useEffect(() => {
    if (visible) chartRef.current?.resize()
  }, [visible])

  useEffect(() => {
    if (!chartRef.current || !points.length) return
    const recent = points.slice(-MAX_POINTS)
    const ds = chartRef.current.data.datasets[0]
    chartRef.current.data.labels = recent.map(() => '')
    ds.data = recent.map(p => p.prob)
    ds.pointBackgroundColor = recent.map(p => p.isAnomaly ? '#ef4444' : '#10b981')
    ds.pointBorderColor     = recent.map(p => p.isAnomaly ? '#ef4444' : '#10b981')
    chartRef.current.update('none')
  }, [points])

  const anomalyCount = points.filter(p => p.isAnomaly).length
  const totalCount   = points.length
  const anomalyRate  = totalCount ? ((anomalyCount / totalCount) * 100).toFixed(1) : '0.0'

  return (
    <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <span className="card-title">📡 Live Monitor</span>
        <button
          className={liveRunning ? styles.stopBtn : 'btn-secondary'}
          onClick={onToggle}
          disabled={!modelsReady}
          title={!modelsReady ? 'Train models first' : undefined}
        >
          {liveRunning ? '⏹ Stop' : '▶ Simulate'}
        </button>
      </div>

      {/* Stats bar */}
      <div className={styles.statsBar}>
        <div className={styles.statItem}>
          <span className={styles.statVal}>{totalCount}</span>
          <span className={styles.statLbl}>packets</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={`${styles.statVal} ${styles.statDanger}`}>{anomalyCount}</span>
          <span className={styles.statLbl}>anomalies</span>
        </div>
        <div className={styles.statDivider} />
        <div className={styles.statItem}>
          <span className={`${styles.statVal} ${parseFloat(anomalyRate) > 20 ? styles.statDanger : styles.statOk}`}>
            {anomalyRate}%
          </span>
          <span className={styles.statLbl}>rate</span>
        </div>
      </div>

      <div className="card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '.9rem', minHeight: 0 }}>
        <div className={styles.chartWrap}>
          <canvas ref={canvasRef} />
        </div>
        <div className={styles.feedHeader}>Recent Events</div>
        <div className={styles.feed}>
          {feed.length === 0 ? (
            <div className={styles.feedEmpty}>
              {modelsReady ? 'Press Simulate to start.' : 'Train models first.'}
            </div>
          ) : (
            [...feed].reverse().slice(0, 10).map((f, i) => (
              <div key={i} className={`${styles.feedRow} ${f.isAnomaly ? styles.anomaly : styles.normal} ${i === 0 ? styles.feedLatest : ''}`}>
                <span className={styles.feedDot} />
                <span className={styles.feedTime}>{f.time}</span>
                <span className={styles.feedLabel}>{f.isAnomaly ? '🚨' : '✅'} {f.label}</span>
                <span className={`${styles.feedScore} ${f.isAnomaly ? styles.scoreRed : styles.scoreGreen}`}>
                  {(f.prob * 100).toFixed(0)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
