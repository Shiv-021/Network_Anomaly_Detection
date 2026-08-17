import { useEffect, useRef, useCallback } from 'react'

/**
 * Generic Server-Sent Events hook.
 * Connects to `url`, calls `onMessage(data)` on each event.
 * Re-connects whenever `url` changes and `enabled` is true.
 * Returns { close } to manually stop the stream.
 */
export default function useSSE(url, onMessage, enabled = true) {
  const esRef = useRef(null)
  const cbRef = useRef(onMessage)
  cbRef.current = onMessage        // always call the latest callback

  const close = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
  }, [])

  useEffect(() => {
    if (!enabled || !url) return
    esRef.current?.close()
    const es = new EventSource(url)
    es.onmessage = (e) => cbRef.current(e.data)
    es.onerror   = () => { /* silently tolerate reconnect */ }
    esRef.current = es
    return () => { es.close(); esRef.current = null }
  }, [url, enabled])

  return { close }
}
