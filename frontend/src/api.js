const BASE = '/api'

export async function fetchRooms() {
  const res = await fetch(`${BASE}/rooms/`)
  if (!res.ok) throw new Error('Failed to fetch rooms')
  return res.json()
}

export async function createRoom(name) {
  const res = await fetch(`${BASE}/rooms/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to create room')
  return data
}

export async function fetchRoom(slug) {
  const res = await fetch(`${BASE}/rooms/${slug}/`)
  if (!res.ok) throw new Error('Room not found')
  return res.json()
}
