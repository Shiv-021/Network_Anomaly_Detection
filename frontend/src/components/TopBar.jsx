import styles from './TopBar.module.css'

export default function TopBar({ health }) {
  return (
    <div className={styles.topbar}>
      <div className={styles.brand}>
        <div className={styles.brandIcon}>🛡</div>
        <div>
          <div className={styles.brandTitle}>Network Anomaly Detection</div>
          <div className={styles.brandSub}>XGBoost · PCA Reconstruction · NSL-KDD · Real-Time Monitor</div>
        </div>
      </div>
      <div className={`${styles.healthPill} ${health.status === 'ok' ? styles.ok : health.status === 'err' ? styles.err : health.status === 'warn' ? styles.warn : ''}`}>
        <span className={styles.healthDot} />
        <span>{health.text}</span>
      </div>
    </div>
  )
}
