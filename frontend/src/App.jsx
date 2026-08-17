import { useState, useEffect, useCallback } from 'react'
import TopBar from './components/TopBar'
import PageTabs from './components/PageTabs'
import LiveStatsBar from './components/LiveStatsBar'
import MonitorTab from './components/monitor/MonitorTab'
import TrainTab from './components/train/TrainTab'
import Lightbox from './components/Lightbox'

export default function App() {
  const [tab, setTab]           = useState('monitor')
  const [lightbox, setLightbox] = useState(null)
  const [health, setHealth]     = useState({ status: 'connecting', text: 'Connecting…' })

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/health')
      const d   = await res.json()
      if (d.status === 'ok') {
        setHealth({ status: 'ok',   text: 'All models loaded' })
      } else {
        setHealth({ status: 'warn', text: 'No models trained yet — use Train Pipeline' })
      }
    } catch {
      setHealth({ status: 'err', text: 'Server unreachable' })
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const t = setInterval(checkHealth, 10000)
    return () => clearInterval(t)
  }, [checkHealth])

  const modelsReady = health.status === 'ok'

  return (
    <div className="wrap">
      <TopBar health={health} />
      <PageTabs tab={tab} setTab={setTab} />

      {tab === 'monitor' && <LiveStatsBar modelsReady={modelsReady} />}

      <MonitorTab visible={tab === 'monitor'} modelsReady={modelsReady} onLightbox={setLightbox} />
      <TrainTab   visible={tab === 'train'}   onLightbox={setLightbox} onTrainDone={checkHealth} />

      {lightbox && (
        <Lightbox
          src={lightbox.src}
          title={lightbox.title}
          onClose={() => setLightbox(null)}
        />
      )}
    </div>
  )
}
