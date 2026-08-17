// Thin wrappers around fetch for the Flask API

export async function fetchHealth() {
  const res = await fetch('/health')
  return res.json()
}

export async function fetchModelInfo() {
  const res = await fetch('/model/info')
  if (!res.ok) throw new Error('Model info unavailable')
  return res.json()
}

export async function fetchPlots() {
  const res = await fetch('/api/plots')
  if (!res.ok) throw new Error('No plots available')
  return res.json()
}

export async function predict(endpoint, payload) {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  return { ok: res.ok, status: res.status, data }
}

export async function uploadCSV(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: fd })
  const data = await res.json()
  return { ok: res.ok, data }
}

export async function useLocalData() {
  const res = await fetch('/api/train/use-local', { method: 'POST' })
  const data = await res.json()
  return { ok: res.ok, data }
}

export async function startTraining(noPlots = false) {
  const res = await fetch('/api/train/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ no_plots: noPlots }),
  })
  const data = await res.json()
  return { ok: res.ok, data }
}

export async function resetTraining() {
  const res = await fetch('/api/train/reset', { method: 'POST' })
  const data = await res.json()
  return { ok: res.ok, data }
}

export async function fetchTrainStatus() {
  const res = await fetch('/api/train/status')
  return res.json()
}
