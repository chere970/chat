import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sun, Moon, MessageSquare, Plus, ArrowRight, Zap, Users, Shield, Phone, Lock } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useUser } from '../context/UserContext'
import { fetchRooms, createRoom } from '../api'
import { formatRelative } from '../utils'
import Avatar from '../components/Avatar'
import './Home.css'

export default function Home() {
  const { theme, toggle } = useTheme()
  const { username, setUsername } = useUser()
  const navigate = useNavigate()
  const [rooms, setRooms] = useState([])
  const [name, setName] = useState(username)
  const [roomName, setRoomName] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [showPhoneField, setShowPhoneField] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchRooms().then(setRooms).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    const displayName = name.trim()
    if (displayName.length < 2) { setError('Name must be at least 2 characters'); return }
    if (!roomName.trim()) { setError('Enter a room name'); return }
    if (showPhoneField && phoneNumber.trim() && !/^\+?[1-9]\d{6,14}$/.test(phoneNumber.trim())) {
      setError('Invalid phone number. Use format like +1234567890')
      return
    }
    setUsername(displayName)
    try {
      const room = await createRoom(roomName.trim(), showPhoneField ? phoneNumber.trim() : '')
      navigate(`/rooms/${room.slug}`)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleJoinRoom = (slug) => {
    if (!username || username.length < 2) {
      setError('Set a display name first')
      return
    }
    navigate(`/rooms/${slug}`)
  }

  return (
    <div className="home">
      <header className="home-header">
        <div className="home-brand">
          <div className="brand-icon"><MessageSquare size={20} /></div>
          <span className="brand-text">Relay</span>
        </div>
        <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      <main className="home-main">
        <section className="hero">
          <div className="hero-badge">
            <Zap size={14} /> Real-time WebSocket Chat
          </div>
          <h1>Conversations that<br/><span className="gradient-text">move at light speed.</span></h1>
          <p className="hero-sub">Pick a name, create or join a room, and start chatting live — powered by Django Channels.</p>

          <form className="create-form" onSubmit={handleCreate}>
            <div className="form-row">
              <div className="field">
                <label>Your display name</label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. Maya"
                  maxLength={32}
                  required
                  id="display-name-input"
                />
              </div>
              <div className="field">
                <label>Room name</label>
                <input
                  type="text"
                  value={roomName}
                  onChange={e => setRoomName(e.target.value)}
                  placeholder="e.g. design-critique"
                  maxLength={64}
                  required
                  id="room-name-input"
                />
              </div>
            </div>

            {showPhoneField && (
              <div className="phone-field-row" style={{ animation: 'slideUp 0.3s ease both' }}>
                <div className="field">
                  <label><Phone size={13} /> Phone number for OTP protection</label>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={e => setPhoneNumber(e.target.value)}
                    placeholder="+1234567890"
                    maxLength={20}
                    id="phone-number-input"
                  />
                  <span className="field-hint">
                    Only users who verify this phone number can join the room.
                  </span>
                </div>
              </div>
            )}

            <div className="form-actions">
              <button type="submit" className="btn-primary" id="create-room-btn">
                <Plus size={18} /> Open Room
              </button>
              <button
                type="button"
                className={`btn-phone-toggle ${showPhoneField ? 'active' : ''}`}
                onClick={() => { setShowPhoneField(!showPhoneField); if (showPhoneField) setPhoneNumber('') }}
                id="toggle-phone-btn"
              >
                {showPhoneField ? <Lock size={16} /> : <Shield size={16} />}
                {showPhoneField ? 'Remove Protection' : 'Add Phone OTP'}
              </button>
            </div>
            {error && <p className="form-error">{error}</p>}
          </form>
        </section>

        <section className="features">
          <div className="feature-card">
            <div className="feature-icon"><Zap size={22} /></div>
            <h3>Instant Messaging</h3>
            <p>Messages broadcast live over WebSockets with zero delay.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Users size={22} /></div>
            <h3>Presence & Typing</h3>
            <p>See who's online and when they're typing in real-time.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Shield size={22} /></div>
            <h3>Phone OTP Rooms</h3>
            <p>Protect rooms with phone number verification for secure access.</p>
          </div>
        </section>

        <section className="rooms-section" aria-labelledby="rooms-heading">
          <div className="section-head">
            <h2 id="rooms-heading">Active Rooms</h2>
            <span className="room-count">{rooms.length} room{rooms.length !== 1 ? 's' : ''}</span>
          </div>
          {loading ? (
            <div className="rooms-loading">
              {[1,2,3].map(i => <div key={i} className="room-skeleton" />)}
            </div>
          ) : rooms.length > 0 ? (
            <ul className="room-list">
              {rooms.map((room, i) => (
                <li key={room.id} style={{ animationDelay: `${i * 0.05}s` }}>
                  <button className="room-card" onClick={() => handleJoinRoom(room.slug)} id={`room-${room.slug}`}>
                    <div className="room-card-avatar">
                      <Avatar name={room.name} size="lg" />
                    </div>
                    <div className="room-card-info">
                      <span className="room-card-name">
                        {room.name}
                        {room.is_protected && (
                          <span className="room-protected-badge" title="OTP protected">
                            <Lock size={12} />
                          </span>
                        )}
                      </span>
                      <span className="room-card-meta">
                        {room.message_count} message{room.message_count !== 1 ? 's' : ''} · {formatRelative(room.created_at)}
                        {room.is_protected && ' · 🔐 Protected'}
                      </span>
                    </div>
                    <ArrowRight size={18} className="room-card-arrow" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-rooms">
              <div className="empty-orb" />
              <p>No rooms yet</p>
              <span>Create the first one above!</span>
            </div>
          )}
        </section>
      </main>

      <footer className="home-footer">
        <p>Built to make your conversations <span className="gradient-text">fast</span> · ❤️</p>
      </footer>
    </div>
  )
}
