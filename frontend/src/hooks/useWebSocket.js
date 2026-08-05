import { useRef, useEffect, useCallback, useState } from 'react'

export function useWebSocket(roomSlug, username, onMessage) {
  const wsRef = useRef(null)
  const reconnectRef = useRef(null)
  const [status, setStatus] = useState('connecting')

  const connect = useCallback(() => {
    if (!roomSlug) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/ws/chat/${roomSlug}/`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      if (username) ws.send(JSON.stringify({ type: 'join', username }))
    }

    ws.onclose = () => {
      setStatus('reconnecting')
      clearTimeout(reconnectRef.current)
      reconnectRef.current = setTimeout(connect, 1500)
    }

    ws.onerror = () => ws.close()

    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch {}
    }
  }, [roomSlug, username, onMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { send, status }
}
