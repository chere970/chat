import { hashColor, initials } from '../utils'
import './Avatar.css'

export default function Avatar({ name, size = 'md', className = '' }) {
  const color = hashColor(name || '')
  return (
    <div
      className={`avatar avatar-${size} ${className}`}
      style={{ '--avatar-bg': color }}
      title={name}
    >
      {initials(name || '?')}
    </div>
  )
}
