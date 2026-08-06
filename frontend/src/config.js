const normalizedBackendOrigin = import.meta.env.VITE_BACKEND_URL?.replace(/\/+$/, '') || ''

export function getApiBase() {
  return normalizedBackendOrigin ? `${normalizedBackendOrigin}/api` : '/api'
}

export function getWebSocketUrl(roomSlug) {
  if (normalizedBackendOrigin) {
    const wsOrigin = normalizedBackendOrigin.replace(/^http/, 'ws')
    return `${wsOrigin}/ws/chat/${roomSlug}/`
  }

  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws/chat/${roomSlug}/`
}