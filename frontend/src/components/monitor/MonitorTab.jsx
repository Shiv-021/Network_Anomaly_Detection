import { useState, useRef, useCallback } from 'react'
import { SAMPLES } from '../../utils/samples'
import { predict } from '../../utils/api'
import { parseResult } from '../../utils/parseResult'
import PredictionForm from './PredictionForm'
import LiveMonitor from './LiveMonitor'
import Verdict from './Verdict'
import AttackChart from './AttackChart'
import ModelInfo from './ModelInfo'
import RawResponse from './RawResponse'
import Thresholds from './Thresholds'
import HistoryTable from './HistoryTable'

const SIM_POOL = Object.values(SAMPLES)

function now() {
  return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function MonitorTab({ visible, modelsReady, onLightbox }) {
  const [result, setResult]         = useState(null)
  const [rawJson, setRawJson]       = useState(null)
  const [history, setHistory]       = useState([])
  const [timelinePoints, setTimePts] = useState([])
  const [feed, setFeed]             = useState([])
  const [liveRunning, setLiveRunning] = useState(false)
  const intervalRef = useRef(null)

  const handleResult = useCallback((r, raw) => {
    setResult(r)
    setRawJson(raw)
    // Add to history
    setHistory(prev => [...prev, {
      time:        now(),
      isAnomaly:   r.isAnomaly,
      mainScore:   r.mainScore,
      endpoint:    r.endpoint,
      attackClass: r.attackClass,
      mixedSignal: r.mixedSignal,
    }])
    // Add to timeline
    setTimePts(prev => [...prev, { prob: r.mainScore, isAnomaly: r.isAnomaly }])
  }, [])

  const runSim = useCallback(async () => {
    const record = SIM_POOL[Math.floor(Math.random() * SIM_POOL.length)]
    try {
      const { ok, data } = await predict('/predict/full', { data: [record] })
      if (!ok) return
      const r = parseResult(data, '/predict/full')
      handleResult(r, JSON.stringify(data, null, 2))
      setFeed(prev => [...prev, {
        time:     now(),
        isAnomaly: r.isAnomaly,
        label:    r.attackClass || r.mainLabel,
        prob:     r.mainScore,
      }])
    } catch { /* ignore sim errors */ }
  }, [handleResult])

  const toggleSim = useCallback(() => {
    if (liveRunning) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
      setLiveRunning(false)
    } else {
      setLiveRunning(true)
      runSim()
      intervalRef.current = setInterval(runSim, 1400)
    }
  }, [liveRunning, runSim])

  const clearHistory = () => {
    setHistory([])
    setTimePts([])
    setFeed([])
  }

  return (
    <div style={{ display: visible ? 'block' : 'none' }}>
      {/* Row 1: Form + Live Monitor */}
      <div className="monitor-grid">
        <PredictionForm onResult={handleResult} modelsReady={modelsReady} />
        <LiveMonitor
          points={timelinePoints}
          liveRunning={liveRunning}
          onToggle={toggleSim}
          feed={feed}
          modelsReady={modelsReady}
          visible={visible}
        />
      </div>

      {/* Row 2: Current Verdict */}
      <Verdict result={result} />

      {/* Row 3: Attack Distribution — full width so its two donut charts get
          real room instead of being squeezed into a 1-of-3 grid column. */}
      <div style={{ marginBottom: '1.2rem' }}>
        <AttackChart history={history} visible={visible} />
      </div>

      {/* Row 4: Model info + Raw response/Thresholds, shifted below */}
      <div className="info-grid">
        <ModelInfo modelsReady={modelsReady} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <RawResponse raw={rawJson} />
          <Thresholds result={result} />
        </div>
      </div>

      {/* Row 5: History table */}
      <HistoryTable history={history} onClear={clearHistory} />
    </div>
  )
}
