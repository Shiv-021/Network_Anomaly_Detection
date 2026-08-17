/**
 * Custom hook managing all training pipeline state.
 * Exposes: { status, dataInfo, logLines, steps, noPlots, setNoPlots,
 *            setData, startTraining, resetTraining }
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { startTraining, resetTraining as apiReset, useLocalData, uploadCSV } from '../utils/api'

const STEP_KEYWORDS = [
  { step: 1, patterns: ['block 1', 'loading csv', 'data load', 'rows loaded', 'reading'] },
  { step: 2, patterns: ['block 2', 'exploratory', 'eda', 'distribution', 'correlation'] },
  { step: 3, patterns: ['block 3', 'feature engineer', 'encoding', 'scaling', 'frequency'] },
  { step: 4, patterns: ['block 4', 'training model', 'xgboost', 'fitting', 'random forest', 'training complete'] },
]

function detectStep(line) {
  const lower = line.toLowerCase()
  for (const { step, patterns } of STEP_KEYWORDS) {
    if (patterns.some(p => lower.includes(p))) return step
  }
  return null
}

const STEP_LABELS = ['Data Loading', 'EDA & Visualisation', 'Feature Engineering', 'Model Training']

export default function useTraining(onTrainDone) {
  const [status,   setStatus]   = useState('idle')
  const [dataInfo, setDataInfo] = useState(null)
  const [logLines, setLogLines] = useState([])
  const [activeStep, setActiveStep] = useState(0)
  const [noPlots, setNoPlots]   = useState(false)
  const [results, setResults]   = useState(null)
  const [resultsError, setResultsError] = useState(null)
  const [logFile, setLogFile]   = useState(null)   // path to full verbose log
  const [trainCount, setTrainCount] = useState(0)  // increments after each training run
  const esRef = useRef(null)

  // Pre-load results from a previous training run when the page first loads
  useEffect(() => {
    fetch('/model/info')
      .then(r => r.ok ? r.json() : null)
      .then(info => {
        if (info && (info.binary_comparison || info.multiclass_comparison)) {
          setResults({
            binary:       info.binary_comparison,
            multiclass:   info.multiclass_comparison,
            unsupervised: info.unsupervised_comparison,
            cv:           info.cv_comparison,
          })
        }
      })
      .catch(err => {
        // Don't fail silently — a malformed comparison JSON (e.g. a stray
        // NaN) will make res.json() throw here, which previously left the
        // Model Comparison card blank with zero indication anything went
        // wrong. Surface it so it's obvious this is a data/backend issue,
        // not "the UI doesn't work".
        console.error('Failed to load /model/info:', err)
        setResultsError('Could not load training metrics — the comparison data may be malformed. Plots below are unaffected.')
      })
  }, [])

  const setData = useCallback((name, mb) => {
    setDataInfo({ name, mb })
  }, [])

  const handleUpload = useCallback(async (file) => {
    setDataInfo(null)
    const { ok, data } = await uploadCSV(file)
    if (!ok) throw new Error(data.error || 'Upload failed')
    setDataInfo({ name: data.filename || file.name, mb: (file.size / 1048576).toFixed(1) })
  }, [])

  const handleUseLocal = useCallback(async () => {
    setDataInfo(null)
    const { ok, data } = await useLocalData()
    if (!ok) throw new Error(data.error || 'Failed to use local data')
    setDataInfo({ name: data.name || 'Network_anomaly_data.csv', mb: data.mb != null ? Number(data.mb).toFixed(1) : '?' })
  }, [])

  const start = useCallback(async () => {
    if (!dataInfo) throw new Error('No data selected')
    setStatus('running')
    setLogLines([])
    setActiveStep(1)
    setResults(null)

    const { ok, data } = await startTraining(noPlots)
    if (!ok) {
      setStatus('error')
      setActiveStep(0)
      throw new Error(data.error || 'Failed to start training')
    }

    // Connect SSE log stream
    esRef.current?.close()
    const es = new EventSource('/api/train/logs')
    esRef.current = es

    es.onmessage = (e) => {
      const raw = e.data
      if (raw === '[HEARTBEAT]') return

      if (raw.startsWith('[STATUS:')) {
        const st = raw.replace('[STATUS:', '').replace(']', '').trim()
        setStatus(st)
        if (st === 'done') setActiveStep(4)
        if (st === 'error') { /* keep step visible */ }
        es.close()
        esRef.current = null

        // After done, fetch results
        if (st === 'done') {
          fetch('/api/train/status')
            .then(r => r.json())
            .then(d => { if (d.log_file) setLogFile(d.log_file) })
            .catch(() => {})
          // Small delay so backend reload_models finishes before we query it
          setTimeout(() => {
            // Bump trainCount unconditionally — new plot PNGs exist on disk
            // the moment training finishes, regardless of whether the
            // /model/info metrics fetch below succeeds. Gating this on the
            // metrics response meant a single malformed comparison JSON
            // could also prevent the Plots Gallery from ever refreshing.
            setTrainCount(c => c + 1)
            setResultsError(null)
            fetch('/model/info')
              .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
              .then(info => {
                setResults({
                  binary:        info.binary_comparison,
                  multiclass:    info.multiclass_comparison,
                  unsupervised:  info.unsupervised_comparison,
                  cv:            info.cv_comparison,
                })
              })
              .catch(err => {
                console.error('Failed to load /model/info after training:', err)
                setResultsError('Training finished, but the metrics comparison data could not be loaded — the comparison JSON may be malformed. Plots below are unaffected.')
              })
          }, 800)
          onTrainDone?.()
        }
        return
      }

      setLogLines(prev => [...prev, raw])

      const s = detectStep(raw)
      if (s) setActiveStep(s)
    }

    es.onerror = () => {
      setLogLines(prev => [...prev, '[SSE connection lost — training may still be running]'])
      es.close()
    }
  }, [dataInfo, noPlots])

  const reset = useCallback(async () => {
    esRef.current?.close()
    esRef.current = null
    await apiReset().catch(() => {})
    setStatus('idle')
    setLogLines([])
    setDataInfo(null)
    setActiveStep(0)
    setResults(null)
    setResultsError(null)
    setLogFile(null)
  }, [])

  return {
    status, dataInfo, logLines, activeStep, noPlots, setNoPlots,
    stepLabels: STEP_LABELS,
    results, resultsError, logFile, trainCount,
    handleUpload, handleUseLocal,
    start, reset,
  }
}
