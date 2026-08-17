import { useEffect, useCallback, useState } from 'react'
import { fetchPlots } from '../utils/api'
import styles from './PlotsGallery.module.css'

const ALL_CAT = 'All'
const CATEGORIES = [ALL_CAT, 'EDA', 'Feature Engineering', 'Training', 'Unsupervised']

export default function PlotsGallery({ onLightbox, refreshKey }) {
  const [plots, setPlots] = useState([])
  const [cat, setCat] = useState(ALL_CAT)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchPlots()
      // data expected: { plots: [{filename, category, title}] }
      setPlots(data.plots || [])
    } catch {
      setPlots([])
    } finally {
      setLoading(false)
    }
  }, [])

  // Reload when refreshKey changes (i.e. after a new training run)
  useEffect(() => { load() }, [load, refreshKey])

  const visible = cat === ALL_CAT ? plots : plots.filter(p => p.category === cat)

  if (loading) return <div className="empty-state">Loading plots…</div>

  return (
    <div>
      <div className={`plot-tabs ${styles.tabs}`}>
        {CATEGORIES.map(c => (
          <button
            key={c}
            className={`plot-tab ${cat === c ? 'active' : ''}`}
            onClick={() => setCat(c)}
          >{c}</button>
        ))}
        <button className="btn-icon" style={{ marginLeft: 'auto' }} onClick={load}>↻ Refresh</button>
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          No plots found.{' '}
          {plots.length === 0
            ? 'Train the model first to generate plots.'
            : `No plots in category "${cat}".`}
        </div>
      ) : (
        <div className="plot-grid">
          {visible.map(p => (
            <div
              key={p.filename}
              className="plot-card"
              onClick={() => onLightbox?.({ src: `/plots/${p.filename}`, title: p.title || p.filename })}
            >
              <img src={`/plots/${p.filename}`} alt={p.title || p.filename} loading="lazy" />
              <div className="plot-label">{p.title || p.filename.replace(/[-_]/g, ' ').replace(/\.png$/, '')}</div>
              <div className="plot-cat-tag">{p.category}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
