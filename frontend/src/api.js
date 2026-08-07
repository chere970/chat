import { getApiBase } from './config'

const BASE = getApiBase()

async function parseJson(res) {
  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    throw new Error(
      res.status === 502 || res.status === 504 || res.status === 500
        ? 'Django backend is not reachable. Start it with: python manage.py runserver'
        : `API returned non-JSON (HTTP ${res.status}). Is the Django server running on :8000?`
    )
  }
  return res.json()
}

export async function fetchRooms() {
  const res = await fetch(`${BASE}/rooms/`)
  if (!res.ok) {
    await parseJson(res).catch(() => {
      throw new Error('Failed to fetch rooms — is Django running on :8000?')
    })
    throw new Error('Failed to fetch rooms')
  }
  return parseJson(res)
}

export async function createRoom(name, phoneNumber = '') {
  let res
  try {
    const body = { name }
    if (phoneNumber) body.phone_number = phoneNumber
    res = await fetch(`${BASE}/rooms/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error('Cannot reach API. Start Django: python manage.py runserver')
  }

  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to create room')
  return data
}

export async function fetchRoom(slug) {
  const res = await fetch(`${BASE}/rooms/${slug}/`)
  if (!res.ok) {
    if (res.status === 404) throw new Error('Room not found')
    throw new Error('Failed to load room — is Django running on :8000?')
  }
  return parseJson(res)
}

export async function sendOTP(phoneNumber, roomSlug) {
  const res = await fetch(`${BASE}/otp/send/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber, room_slug: roomSlug }),
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to send OTP')
  return data
}

export async function verifyOTP(phoneNumber, roomSlug, code) {
  const res = await fetch(`${BASE}/otp/verify/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber, room_slug: roomSlug, code }),
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Invalid OTP')
  return data
}
