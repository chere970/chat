import './TypingIndicator.css'

export default function TypingIndicator({ users }) {
  if (!users.length) return null
  const label = users.length === 1 ? `${users[0]} is typing` : `${users.length} people typing`
  return (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span /><span /><span />
      </div>
      <span className="typing-label">{label}</span>
    </div>
  )
}
