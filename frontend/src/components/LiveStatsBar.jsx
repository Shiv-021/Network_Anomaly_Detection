import { useState, useCallback } from 'react'
import useSSE from '../hooks/useSSE'
import styles from './LiveStatsBar.module.css'

const ZERO = { total: 0, anomalies: 0, normal: 0, per_minute: 0, uptime: 0 }

export default function LiveStatsBar({ modelsReady }) {
  const [stats, setStats] = useState(ZERO)

  const handleMsg = useCallback((raw) => {
    try { setStats(JSON.parse(raw)) } catch { /* ignore */ }
  }, [])

  useSSE('/api/events', handleMsg, modelsReady)

  const anomalyPct = stats.total ? ((stats.anomalies / stats.total) * 100).toFixed(1) : '0.0'
  const normalPct  = stats.total ? ((stats.normal  / stats.total) * 100).toFixed(1) : '0.0'
  const h = Math.floor(stats.uptime / 3600)
  const m = Math.floor((stats.uptime % 3600) / 60)
  const s = stats.uptime % 60
  const uptime = (h ? h + 'h ' : '') + (m ? m + 'm ' : '') + s + 's'

  return (
    <div className={styles.bar}>
      <StatCard icon="📡" label="Live Status" value="Active" sub={`Uptime: ${uptime}`} />
      <StatCard icon="📊" label="Total Predictions" value={stats.total} sub="since server start" />
      <StatCard icon="🚨" label="Anomalies" value={stats.anomalies} sub={`${anomalyPct}% of total`} valueClass={styles.anomaly} />
      <StatCard icon="✅" label="Normal Traffic" value={stats.normal} sub={`${normalPct}% of total`} valueClass={styles.normalc} />
      <StatCard icon="⚡" label="Per Minute" value={stats.per_minute} sub="predictions / min" />
    </div>
  )
}

function StatCard({ icon, label, value, sub, valueClass = '' }) {
  return (
    <div className={styles.card}>
      <div className={styles.label}>{label}</div>
      <div className={`${styles.value} ${valueClass}`}>{value}</div>
      <div className={styles.sub}>{sub}</div>
      <div className={styles.icon}>{icon}</div>
    </div>
  )
}
