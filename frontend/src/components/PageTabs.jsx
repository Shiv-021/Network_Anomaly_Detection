import styles from './PageTabs.module.css'

const TABS = [
  { id: 'monitor', label: 'Monitor & Test', dotColor: 'var(--success)' },
  { id: 'train',   label: 'Train Pipeline', dotColor: 'var(--warn)' },
]

export default function PageTabs({ tab, setTab }) {
  return (
    <div className={styles.tabs}>
      {TABS.map(t => (
        <button
          key={t.id}
          className={`${styles.tab} ${tab === t.id ? styles.active : ''}`}
          onClick={() => setTab(t.id)}
        >
          <span className={styles.dot} style={{ background: t.dotColor }} />
          {t.label}
        </button>
      ))}
    </div>
  )
}
