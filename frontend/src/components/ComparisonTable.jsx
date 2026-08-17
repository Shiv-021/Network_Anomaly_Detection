/**
 * Reusable model comparison table.
 * Props:
 *   title  — section heading string
 *   data   — { models: [{name/Model, ...metrics}], best: "XGBoost" }
 */

// Columns that are proportions (0–1) and should be displayed as percentages
const PCT_COLS = new Set(['accuracy', 'f1', 'precision', 'recall'])
// Columns shown as raw 4-decimal floats (not multiplied by 100)
const RAW_COLS = new Set(['roc-auc', 'silhouette', 'davies-bouldin',
  'cv f1', 'f1 std', 'cv roc-auc', 'auc std'])

function fmtCell(col, val) {
  if (typeof val !== 'number') return val ?? '—'
  const key = col.toLowerCase()
  if (PCT_COLS.has(key))  return (val * 100).toFixed(1) + '%'
  if (RAW_COLS.has(key))  return val.toFixed(4)
  // Unknown numeric — if looks like a proportion render as %; otherwise raw
  return (val >= 0 && val <= 1) ? (val * 100).toFixed(1) + '%' : val.toFixed(4)
}

export default function ComparisonTable({ title, data }) {
  if (!data || !data.models || data.models.length === 0) return null

  const nameKey = Object.prototype.hasOwnProperty.call(data.models[0], 'name') ? 'name' : 'Model'
  // Union of keys across ALL rows, not just the first — models in this
  // pipeline don't all report the same metrics (e.g. only the PCA row has
  // "ROC-AUC"; Isolation Forest has none). Deriving columns from row 0 alone
  // silently drops any column that first appears further down the list.
  const colSet  = new Set()
  data.models.forEach(m => Object.keys(m).forEach(k => colSet.add(k)))
  colSet.delete(nameKey)
  const cols = Array.from(colSet)

  return (
    <div className="cmp-section">
      {title && (
        <div className="cmp-label">
          {title}
          {data.best && <span className="best-badge">★ {data.best}</span>}
        </div>
      )}
      <table className="cmp-table">
        <thead>
          <tr>
            <th>Model</th>
            {cols.map(c => <th key={c}>{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.models.map(m => (
            <tr key={m[nameKey]} className={m[nameKey] === data.best ? 'best-row' : ''}>
              <td>{m[nameKey]}</td>
              {cols.map(c => (
                <td key={c}>{fmtCell(c, m[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
