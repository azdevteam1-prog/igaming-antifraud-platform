import { useEffect, useRef, useCallback } from 'react'

export function useWebSocket(onMessage: (data: any) => void) {
  const ws = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${window.location.host}/ws/transactions`
    ws.current = new WebSocket(url)
    ws.current.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch {}
    }
    ws.current.onclose = () => {
      setTimeout(connect, 2000) // reconnect
    }
  }, [onMessage])

  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])
}
