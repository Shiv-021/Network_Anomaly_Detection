import { useState, useCallback } from 'react'
import { fetchModelInfo } from '../utils/api'

export default function useModelInfo() {
  const [info, setInfo]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await fetchModelInfo()
      setInfo(d)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  return { info, loading, error, refresh }
}
