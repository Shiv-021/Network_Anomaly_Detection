import { useRef, useEffect } from 'react'
import Chart from 'chart.js/auto'

const COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#6366f1','#0ea5e9','#8b5cf6','#ec4899','#14b8a6','#f97316','#a3e635','#fb7185']

function MiniDonut({ title, labels, values, colors, visible }) {
  const canvasRef = useRef(null)
  const chartRef  = useRef(null)

  useEffect(() => {
    if (!canvasRef.current || labels.length === 0) return
    chartRef.current?.destroy()
    chartRef.current = new Chart(canvasRef.current, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#0d1526',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 9, padding: 6 }
          },
          tooltip: {
            callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw.toFixed(1)}%` }
          },
          title: {
            display: true,
            text: title,
            color: '#94a3b8',
            font: { size: 11, weight: '600' },
            padding: { bottom: 6 },
          }
        }
      }
    })
    return () => { chartRef.current?.destroy(); chartRef.current = null }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labels.join(','), values.join(',')])

  // MonitorTab is never unmounted when you switch to the Train tab — it's
  // just toggled with `display: none` (so Simulate keeps running in the
  // background). Chart.js's resize-observer doesn't reliably fire when a
  // display:none parent becomes visible again, so the canvas keeps
  // whatever internal buffer size it last had and renders stretched/
  // distorted ("haywire") until something forces a recompute. Force one
  // explicitly the moment this tab becomes the visible one again.
  useEffect(() => {
    if (visible) chartRef.current?.resize()
  }, [visible])

  return <canvas ref={canvasRef} />
}

export default function AttackChart({ history, visible }) {
  if (history.length === 0) {
    return (
      <div className="card">
        <div className="card-header"><span className="card-title">🎯 Attack Distribution</span></div>
        <div className="card-body">
          <div className="empty-state">Run predictions to see attack class breakdown.</div>
        </div>
      </div>
    )
  }

  // Binary distribution
  const binaryDist = { Normal: 0, Anomaly: 0 }
  for (const item of history) {
    if (item.isAnomaly) binaryDist.Anomaly++
    else binaryDist.Normal++
  }
  const binaryLabels = Object.keys(binaryDist)
  const binaryTotal  = history.length
  const binaryValues = binaryLabels.map(k => (binaryDist[k] / binaryTotal) * 100)

  // Multiclass distribution (only items that have an attackClass)
  const classDist = {}
  for (const item of history) {
    const k = item.attackClass
    if (k && k !== '–' && k !== '') classDist[k] = (classDist[k] || 0) + 1
  }
  const classLabels = Object.keys(classDist).sort((a, b) => classDist[b] - classDist[a])
  const classTotal  = classLabels.reduce((s, k) => s + classDist[k], 0)
  const classValues = classLabels.map(k => (classDist[k] / classTotal) * 100)

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🎯 Attack Distribution</span>
        <span className="badge badge-warn">{history.length} samples</span>
      </div>
      <div className="card-body" style={{ display: 'flex', gap: '1rem' }}>
        <div style={{ flex: 1, height: 230 }}>
          <MiniDonut
            title="Binary"
            labels={binaryLabels}
            values={binaryValues}
            colors={['#10b981', '#ef4444']}
            visible={visible}
          />
        </div>
        <div style={{ flex: 1, height: 230 }}>
          {classLabels.length > 0 ? (
            <MiniDonut
              title="Attack Type"
              labels={classLabels}
              values={classValues}
              colors={COLORS.slice(0, classLabels.length)}
              visible={visible}
            />
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text3)', fontSize: '.78rem', textAlign: 'center' }}>
              Use Full Analysis or<br />Multiclass mode to see<br />attack type breakdown.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

