const normalizedBackendOrigin = import.meta.env.VITE_BACKEND_URL?.replace(/\/+$/, '') || ''

export function getApiBase() {
  return normalizedBackendOrigin ? `${normalizedBackendOrigin}/api` : '/api'
}

export function getWebSocketUrl(roomSlug, accessToken = '') {
  const tokenQuery = accessToken ? `?token=${encodeURIComponent(accessToken)}` : ''

  if (normalizedBackendOrigin) {
    const wsOrigin = normalizedBackendOrigin.replace(/^http/, 'ws')
    return `${wsOrigin}/ws/chat/${roomSlug}/${tokenQuery}`
  }

  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws/chat/${roomSlug}/${tokenQuery}`
}