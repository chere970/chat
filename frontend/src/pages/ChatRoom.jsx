import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Sun, Moon, Users, Wifi, WifiOff, Loader } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useUser } from '../context/UserContext'
import { useWebSocket } from '../hooks/useWebSocket'
import { fetchRoom } from '../api'
import { playNotificationSound } from '../utils'
import Avatar from '../components/Avatar'
import MessageBubble from '../components/MessageBubble'
import TypingIndicator from '../components/TypingIndicator'
import './ChatRoom.css'

export default function ChatRoom() {
  const { roomSlug } = useParams()
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()
  const { username, setUsername } = useUser()

  const [room, setRoom] = useState(null)
  const [messages, setMessages] = useState([])
  const [reactions, setReactions] = useState({})
  const [input, setInput] = useState('')
  const [onlineUsers, setOnlineUsers] = useState([])
  const [typingUsers, setTypingUsers] = useState([])
  const [showSidebar, setShowSidebar] = useState(false)
  const [needsName, setNeedsName] = useState(!username)
  const [nameInput, setNameInput] = useState('')
  const [error, setError] = useState('')

  const listRef = useRef(null)
  const inputRef = useRef(null)
  const seenIds = useRef(new Set())
  const typingTimeout = useRef(null)
  const isTypingRef = useRef(false)
  const typingTimers = useRef({})

  useEffect(() => {
    fetchRoom(roomSlug).then(setRoom).catch(() => navigate('/'))
  }, [roomSlug, navigate])

  const handleWsMessage = useCallback((data) => {
    if (data.type === 'history') {
      const msgs = (data.messages || []).filter(m => {
        if (seenIds.current.has(m.id)) return false
        seenIds.current.add(m.id)
        return true
      })
      setMessages(prev => [...prev, ...msgs])
    } else if (data.type === 'chat_message') {
      if (!seenIds.current.has(data.id)) {
        seenIds.current.add(data.id)
        setMessages(prev => [...prev, data])
        if (data.username !== username) playNotificationSound()
      }
    } else if (data.type === 'presence') {
      setOnlineUsers(data.users || [])
    } else if (data.type === 'typing') {
      if (data.is_typing) {
        setTypingUsers(prev => prev.includes(data.username) ? prev : [...prev, data.username])
        clearTimeout(typingTimers.current[data.username])
        typingTimers.current[data.username] = setTimeout(() => {
          setTypingUsers(prev => prev.filter(u => u !== data.username))
        }, 3000)
      } else {
        setTypingUsers(prev => prev.filter(u => u !== data.username))
      }
    } else if (data.type === 'reaction') {
      setReactions(prev => ({ ...prev, [data.message_id]: data.reactions }))
    }
  }, [username])

  const { send, status } = useWebSocket(
    needsName ? null : roomSlug,
    username,
    handleWsMessage
  )

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages, typingUsers])

  const handleSend = (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    send({ type: 'chat_message', message: text })
    setInput('')
    isTypingRef.current = false
    send({ type: 'typing', is_typing: false })
    inputRef.current?.focus()
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    if (!isTypingRef.current) {
      isTypingRef.current = true
      send({ type: 'typing', is_typing: true })
    }
    clearTimeout(typingTimeout.current)
    typingTimeout.current = setTimeout(() => {
      isTypingRef.current = false
      send({ type: 'typing', is_typing: false })
    }, 2000)
  }

  const handleReact = (messageId, emoji) => {
    send({ type: 'reaction', message_id: messageId, emoji })
  }

  const handleSetName = (e) => {
    e.preventDefault()
    const n = nameInput.trim()
    if (n.length < 2) { setError('Name must be at least 2 characters'); return }
    setUsername(n)
    setNeedsName(false)
  }

  if (!room) {
    return (
      <div className="chat-loading">
        <Loader size={32} className="spin" />
        <p>Loading room...</p>
      </div>
    )
  }

  if (needsName) {
    return (
      <div className="name-gate">
        <div className="name-gate-card">
          <h2>Join {room.name}</h2>
          <p>Choose a display name to start chatting.</p>
          <form onSubmit={handleSetName}>
            <input
              type="text" value={nameInput} onChange={e => setNameInput(e.target.value)}
              placeholder="Your display name" maxLength={32} required autoFocus
              id="join-name-input"
            />
            <button type="submit" className="btn-join" id="join-room-btn">Enter Room</button>
            {error && <p className="gate-error">{error}</p>}
          </form>
        </div>
      </div>
    )
  }

  const statusIcon = status === 'connected'
    ? <Wifi size={14} />
    : <WifiOff size={14} />
  const statusLabel = status === 'connected' ? 'Live' : status === 'reconnecting' ? 'Reconnecting…' : 'Connecting…'

  return (
    <div className="chatroom">
      <header className="chat-header">
        <button className="back-btn" onClick={() => navigate('/')} aria-label="Back" id="back-btn">
          <ArrowLeft size={18} />
        </button>
        <div className="header-info">
          <Avatar name={room.name} size="md" />
          <div className="header-text">
            <div className="header-title">
              <span className="header-brand">Relay</span>
              <span className="header-sep">/</span>
              <h1>{room.name}</h1>
            </div>
            <div className="header-status">
              <span className={`status-dot status-${status}`} />
              <span className="status-label">{statusLabel}</span>
              {onlineUsers.length > 0 && (
                <span className="online-count">· {onlineUsers.length} online</span>
              )}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button className="icon-btn" onClick={() => setShowSidebar(!showSidebar)} aria-label="Toggle users" id="users-btn">
            <Users size={18} />
          </button>
          <button className="icon-btn" onClick={toggle} aria-label="Toggle theme" id="theme-btn">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className="user-chip" title={`Signed in as ${username}`}>
            <Avatar name={username} size="sm" />
            <span>{username}</span>
          </div>
        </div>
      </header>

      <div className="chat-body">
        <div className="chat-messages-area">
          <div className="message-list" ref={listRef} role="log" aria-live="polite">
            {messages.length === 0 ? (
              <div className="empty-chat">
                <div className="empty-orb" />
                <p>Room is quiet</p>
                <span>Send the first message!</span>
              </div>
            ) : (
              messages.map((msg, i) => {
                const prev = messages[i - 1]
                const isStacked = prev && prev.username === msg.username
                return (
                  <MessageBubble
                    key={msg.id}
                    msg={{ ...msg, _myUsername: username }}
                    isMine={msg.username === username}
                    isStacked={isStacked}
                    onReact={handleReact}
                    reactions={reactions[msg.id]}
                  />
                )
              })
            )}
            <TypingIndicator users={typingUsers} />
          </div>

          <form className="composer" onSubmit={handleSend} autoComplete="off">
            <div className="composer-field">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={handleInputChange}
                placeholder="Write a message…"
                maxLength={1000}
                required
                id="chat-input"
              />
            </div>
            <button type="submit" className="send-btn" aria-label="Send" id="send-btn">
              <Send size={18} />
            </button>
          </form>
        </div>

        {showSidebar && (
          <aside className="users-sidebar">
            <h3>Online — {onlineUsers.length}</h3>
            <ul>
              {onlineUsers.map(u => (
                <li key={u} className={u === username ? 'is-you' : ''}>
                  <Avatar name={u} size="sm" />
                  <span>{u}</span>
                  {u === username && <span className="you-badge">you</span>}
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </div>
  )
}
