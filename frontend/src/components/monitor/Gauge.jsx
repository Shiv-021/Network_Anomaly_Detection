import { useRef, useEffect } from 'react'
import styles from './Gauge.module.css'

export default function Gauge({ value }) {
  // value: 0-1 where 0 = safe, 1 = danger
  const ref = useRef(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    canvas.width  = 160 * dpr
    canvas.height = 90  * dpr
    canvas.style.width  = '160px'
    canvas.style.height = '90px'
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)

    const cx = 80, cy = 82, r = 62
    ctx.clearRect(0, 0, 160, 90)

    // Background track
    ctx.beginPath()
    ctx.arc(cx, cy, r, Math.PI, 2 * Math.PI)
    ctx.strokeStyle = '#1e3a5f'
    ctx.lineWidth = 11
    ctx.lineCap = 'round'
    ctx.stroke()

    // Value arc
    const safe = Math.max(0, Math.min(1, value))
    if (safe > 0) {
      const g = ctx.createLinearGradient(cx - r, 0, cx + r, 0)
      g.addColorStop(0,   '#10b981')
      g.addColorStop(0.5, '#f59e0b')
      g.addColorStop(1,   '#ef4444')
      ctx.beginPath()
      ctx.arc(cx, cy, r, Math.PI, Math.PI + safe * Math.PI)
      ctx.strokeStyle = g
      ctx.lineWidth = 11
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    // Score text
    ctx.fillStyle = safe > 0.6 ? '#fca5a5' : safe > 0.3 ? '#fcd34d' : '#6ee7b7'
    ctx.font = 'bold 18px JetBrains Mono, monospace'
    ctx.textAlign = 'center'
    ctx.fillText((safe * 100).toFixed(0) + '%', cx, cy - 6)
    ctx.fillStyle = '#64748b'
    ctx.font = '10px Inter, sans-serif'
    ctx.fillText('risk score', cx, cy + 8)
  }, [value])

  return <canvas ref={ref} className={styles.canvas} />
}
