import { formatTime } from '../utils'
import Avatar from './Avatar'
import './MessageBubble.css'

const QUICK_EMOJIS = ['👍', '❤️', '😂', '🔥', '👀', '🎉']

export default function MessageBubble({ msg, isMine, isStacked, onReact, reactions }) {
  return (
    <article className={`msg ${isMine ? 'msg-mine' : ''} ${isStacked ? 'msg-stacked' : ''}`}>
      <div className="msg-avatar-col">
        {!isStacked && <Avatar name={msg.username} size="md" />}
      </div>
      <div className="msg-content">
        {!isStacked && (
          <div className="msg-meta">
            <span className="msg-user">{msg.username}</span>
            <time dateTime={msg.created_at}>{formatTime(msg.created_at)}</time>
          </div>
        )}
        <div className="msg-bubble">
          <p>{msg.message}</p>
          {reactions && Object.keys(reactions).length > 0 && (
            <div className="msg-reactions">
              {Object.entries(reactions).map(([emoji, users]) => (
                <button
                  key={emoji}
                  className={`reaction-chip ${users.includes(msg._myUsername) ? 'reaction-mine' : ''}`}
                  onClick={() => onReact(msg.id, emoji)}
                  title={users.join(', ')}
                >
                  {emoji} <span>{users.length}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="msg-actions">
          {QUICK_EMOJIS.map(e => (
            <button key={e} className="react-btn" onClick={() => onReact(msg.id, e)} title={`React ${e}`}>{e}</button>
          ))}
        </div>
      </div>
    </article>
  )
}
