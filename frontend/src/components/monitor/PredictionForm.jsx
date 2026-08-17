import { useState } from 'react'
import { SAMPLES, SAMPLE_BUTTONS } from '../../utils/samples'
import { predict } from '../../utils/api'
import { parseResult } from '../../utils/parseResult'
import styles from './PredictionForm.module.css'

const ENDPOINTS = [
  { value: '/predict',                label: 'Binary',         desc: 'Normal vs Anomaly' },
  { value: '/predict/attack-type',    label: 'Attack Type',    desc: 'Multi-class category' },
  { value: '/predict/reconstruction', label: 'Reconstruction', desc: 'PCA unsupervised score' },
  { value: '/predict/full',           label: 'Full Analysis',  desc: 'All three combined' },
]

const PROTOCOLS = ['tcp', 'udp', 'icmp']
const FLAGS     = ['SF', 'S0', 'S1', 'S2', 'S3', 'REJ', 'RSTO', 'RSTOS0', 'RSTR', 'OTH', 'SH']
const SERVICES  = [
  'http','ftp_data','ftp','smtp','ssh','telnet','private','domain_u','domain',
  'irc','finger','auth','pop_3','pop_2','nntp','uucp','gopher','netbios_ns',
  'netbios_dgm','netbios_ssn','time','ecr_i','eco_i','icmp','other',
]

// Grouped field definitions
const FIELD_GROUPS = [
  {
    title: 'Connection',
    fields: [
      { key: 'duration',     label: 'Duration (s)',   type: 'int',    min: 0 },
      { key: 'protocoltype', label: 'Protocol',       type: 'select', opts: PROTOCOLS },
      { key: 'service',      label: 'Service',        type: 'select', opts: SERVICES },
      { key: 'flag',         label: 'Flag',           type: 'select', opts: FLAGS },
      { key: 'srcbytes',     label: 'Src Bytes',      type: 'int',    min: 0 },
      { key: 'dstbytes',     label: 'Dst Bytes',      type: 'int',    min: 0 },
      { key: 'land',         label: 'Land',           type: 'bool' },
      { key: 'wrongfragment',label: 'Wrong Fragment', type: 'int',    min: 0 },
      { key: 'urgent',       label: 'Urgent',         type: 'int',    min: 0 },
    ],
  },
  {
    title: 'Login / Access',
    fields: [
      { key: 'hot',             label: 'Hot',              type: 'int',  min: 0 },
      { key: 'numfailedlogins', label: 'Failed Logins',    type: 'int',  min: 0 },
      { key: 'loggedin',        label: 'Logged In',        type: 'bool' },
      { key: 'numcompromised',  label: 'Compromised',      type: 'int',  min: 0 },
      { key: 'rootshell',       label: 'Root Shell',       type: 'bool' },
      { key: 'suattempted',     label: 'SU Attempted',     type: 'bool' },
      { key: 'numroot',         label: 'Num Root',         type: 'int',  min: 0 },
      { key: 'numfilecreations',label: 'File Creations',   type: 'int',  min: 0 },
      { key: 'numshells',       label: 'Shells',           type: 'int',  min: 0 },
      { key: 'numaccessfiles',  label: 'Access Files',     type: 'int',  min: 0 },
      { key: 'ishostlogin',     label: 'Host Login',       type: 'bool' },
      { key: 'isguestlogin',    label: 'Guest Login',      type: 'bool' },
    ],
  },
  {
    title: 'Traffic (2-second window)',
    fields: [
      { key: 'count',         label: 'Count',          type: 'int',   min: 0, max: 511 },
      { key: 'srvcount',      label: 'Srv Count',      type: 'int',   min: 0, max: 511 },
      { key: 'serrorrate',    label: 'SYN Error Rate', type: 'float', step: 0.01 },
      { key: 'srvserrorrate', label: 'Srv SYN Err',    type: 'float', step: 0.01 },
      { key: 'rerrorrate',    label: 'REJ Error Rate', type: 'float', step: 0.01 },
      { key: 'srvrerrorrate', label: 'Srv REJ Err',    type: 'float', step: 0.01 },
      { key: 'samesrvrate',   label: 'Same Srv Rate',  type: 'float', step: 0.01 },
      { key: 'diffsrvrate',   label: 'Diff Srv Rate',  type: 'float', step: 0.01 },
      { key: 'srvdiffhostrate',label:'Srv Diff Host',  type: 'float', step: 0.01 },
    ],
  },
  {
    title: 'Destination Host',
    fields: [
      { key: 'dsthostcount',           label: 'Dst Host Count',       type: 'int',   min: 0, max: 255 },
      { key: 'dsthostsrvcount',        label: 'Dst Srv Count',        type: 'int',   min: 0, max: 255 },
      { key: 'dsthostsamesrvrate',     label: 'Same Srv Rate',        type: 'float', step: 0.01 },
      { key: 'dsthostdiffsrvrate',     label: 'Diff Srv Rate',        type: 'float', step: 0.01 },
      { key: 'dsthostsamesrcportrate', label: 'Same Src Port Rate',   type: 'float', step: 0.01 },
      { key: 'dsthostsrvdiffhostrate', label: 'Srv Diff Host Rate',   type: 'float', step: 0.01 },
      { key: 'dsthostserrorrate',      label: 'SYN Error Rate',       type: 'float', step: 0.01 },
      { key: 'dsthostsrvserrorrate',   label: 'Srv SYN Err Rate',     type: 'float', step: 0.01 },
      { key: 'dsthostrerrorrate',      label: 'REJ Error Rate',       type: 'float', step: 0.01 },
      { key: 'dsthostsrvrerrorrate',   label: 'Srv REJ Err Rate',     type: 'float', step: 0.01 },
    ],
  },
]

function initFields(sample) {
  const out = {}
  FIELD_GROUPS.forEach(g => g.fields.forEach(f => { out[f.key] = String(sample[f.key] ?? 0) }))
  return out
}

const GROUP_ICONS = ['🔗', '🔐', '📊', '🖥️']

export default function PredictionForm({ onResult, modelsReady }) {
  const [ep, setEp]             = useState('/predict/full')
  const [fields, setFields]     = useState(() => initFields(SAMPLES.normal))
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [activeGroup, setActiveGroup] = useState(0)

  const loadSample = (key) => { setFields(initFields(SAMPLES[key])); setError(null) }

  const set = (key, val) => setFields(prev => ({ ...prev, [key]: val }))

  const buildRecord = () => {
    const rec = {}
    FIELD_GROUPS.forEach(g => g.fields.forEach(f => {
      const v = fields[f.key]
      rec[f.key] = f.type === 'float' ? parseFloat(v) || 0
                 : f.type === 'bool'  ? (v === 'true' || v === '1' ? 1 : 0)
                 : f.type === 'select'? v
                 : parseInt(v, 10) || 0
    }))
    return rec
  }

  const analyse = async () => {
    setError(null)
    setLoading(true)
    try {
      const { ok, data } = await predict(ep, { data: [buildRecord()] })
      if (!ok) { setError(data.error || `Error ${data.status}`); return }
      onResult(parseResult(data, ep), JSON.stringify(data, null, 2))
    } catch {
      setError('Network error — is the server running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🔬 Connection Record</span>
      </div>
      <div className="card-body">

        {/* Analysis mode */}
        <div className={styles.section}>
          <div className={styles.label}>Analysis Mode</div>
          <div className={styles.epGrid}>
            {ENDPOINTS.map(e => (
              <button key={e.value}
                className={`${styles.epBtn} ${ep === e.value ? styles.epActive : ''}`}
                onClick={() => setEp(e.value)}>
                <span className={styles.epLabel}>{e.label}</span>
                <span className={styles.epDesc}>{e.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Sample buttons */}
        <div className={styles.section}>
          <div className={styles.label}>Load Sample</div>
          <div className={styles.sampleWrap}>
            {SAMPLE_BUTTONS.map(s => (
              <button key={s.key} className={styles.sampleBtn}
                style={{ '--sc': s.group === 'Normal' ? 'var(--success)'
                               : s.group === 'DoS'    ? 'var(--danger)'
                               : s.group === 'U2R'    ? '#a855f7'
                               : s.group === 'R2L'    ? '#0ea5e9'
                               : 'var(--warn)' }}
                onClick={() => loadSample(s.key)}>{s.label}</button>
            ))}
          </div>
        </div>

        {/* Field group tabs */}
        <div className={styles.section}>
          <div className={styles.tabBar}>
            {FIELD_GROUPS.map((g, i) => (
              <button key={g.title}
                className={`${styles.tabBtn} ${activeGroup === i ? styles.tabActive : ''}`}
                onClick={() => setActiveGroup(i)}>
                <span>{GROUP_ICONS[i]}</span>
                <span>{g.title}</span>
                <span className={styles.tabCount}>{g.fields.length}</span>
              </button>
            ))}
          </div>
          <div className={styles.fieldGrid}>
            {FIELD_GROUPS[activeGroup].fields.map(f => (
              <div key={f.key} className={styles.fieldRow}>
                <label className={styles.fieldLabel}>{f.label}</label>
                {f.type === 'select' ? (
                  <select className={styles.fieldInput} value={fields[f.key]}
                    onChange={e => set(f.key, e.target.value)}>
                    {f.opts.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : f.type === 'bool' ? (
                  <select className={styles.fieldInput} value={fields[f.key]}
                    onChange={e => set(f.key, e.target.value)}>
                    <option value="0">0 — No</option>
                    <option value="1">1 — Yes</option>
                  </select>
                ) : (
                  <input type="number" className={styles.fieldInput}
                    value={fields[f.key]}
                    min={f.min ?? undefined}
                    max={f.max ?? undefined}
                    step={f.step ?? 1}
                    onChange={e => set(f.key, e.target.value)} />
                )}
              </div>
            ))}
          </div>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        {!modelsReady && (
          <div className={styles.error} style={{ background:'rgba(245,158,11,.1)', borderColor:'rgba(245,158,11,.3)', color:'#fcd34d' }}>
            ⚠️ No trained models yet — go to Train Pipeline tab first.
          </div>
        )}

        <button className="btn-primary" style={{ width:'100%' }}
          onClick={analyse} disabled={loading || !modelsReady}>
          {loading ? '⏳ Analysing…' : '⚡ Analyse'}
        </button>
      </div>
    </div>
  )
}
