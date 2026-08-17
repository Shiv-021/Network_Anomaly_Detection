import { useState } from 'react'
import useTraining from '../../hooks/useTraining'
import DataSource from './DataSource'
import TrainProgress from './TrainProgress'
import TrainLog from './TrainLog'
import TrainResults from './TrainResults'
import PlotsGallery from '../PlotsGallery'

export default function TrainTab({ visible, onLightbox, onTrainDone }) {
  const training = useTraining(onTrainDone)
  const [startError, setStartError] = useState(null)

  const handleStart = async () => {
    setStartError(null)
    try { await training.start() }
    catch (e) { setStartError(e.message) }
  }

  return (
    <div style={{ display: visible ? 'block' : 'none' }}>
      {/* Row 1: Data source + pipeline options */}
      <div className="main-grid">
        <DataSource
          dataInfo={training.dataInfo}
          onUpload={training.handleUpload}
          onUseLocal={training.handleUseLocal}
          disabled={training.status === 'running'}
        />
        <TrainProgress
          stepLabels={training.stepLabels}
          activeStep={training.activeStep}
          status={training.status}
          noPlots={training.noPlots}
          onTogglePlots={training.setNoPlots}
        />
      </div>

      {startError && (
        <div style={{
          padding: '.6rem .9rem',
          marginBottom: '1.2rem',
          background: 'rgba(239,68,68,.1)',
          border: '1px solid rgba(239,68,68,.25)',
          borderRadius: 'var(--r-sm)',
          color: '#fca5a5',
          fontSize: '.8rem',
        }}>{startError}</div>
      )}

      {/* Row 2: Log + start button */}
      <TrainLog
        logLines={training.logLines}
        status={training.status}
        onStart={handleStart}
        onReset={training.reset}
        canStart={!!training.dataInfo}
        logFile={training.logFile}
      />

      {training.resultsError && (
        <div style={{
          padding: '.6rem .9rem',
          marginBottom: '1.2rem',
          background: 'rgba(239,68,68,.1)',
          border: '1px solid rgba(239,68,68,.25)',
          borderRadius: 'var(--r-sm)',
          color: '#fca5a5',
          fontSize: '.8rem',
        }}>{training.resultsError}</div>
      )}

      {/* Row 3: Model comparison metrics (shown when training finished this session OR models already exist) */}
      {training.results && <TrainResults results={training.results} />}

      {/* Row 4: Generated plots — deliberately independent of the metrics fetch above,
          so a failed/slow /model/info call never hides plots that already exist on disk. */}
      <div className="card">
        <div className="card-header"><span className="card-title">📈 Generated Plots</span></div>
        <div className="card-body">
          <PlotsGallery onLightbox={onLightbox} refreshKey={training.trainCount} />
        </div>
      </div>
    </div>
  )
}
