import styles from './HistoryItem.module.css'

function formatDate(ts) {
  const diff = Math.floor((Date.now() - ts) / 86_400_000)
  if (diff === 0) return 'Hoy'
  if (diff === 1) return 'Ayer'
  if (diff < 7) return `Hace ${diff} días`
  return new Date(ts).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
}

export default function HistoryItem({ chat, isActive, onSelect, onDelete }) {
  return (
    <div
      className={`${styles.item} ${isActive ? styles.active : ''}`}
      onClick={() => onSelect(chat.id)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onSelect(chat.id)}
      aria-current={isActive ? 'page' : undefined}
    >
      <div className={styles.title}>{chat.title}</div>
      <div className={styles.meta}>{formatDate(chat.createdAt)}</div>

      <button
        className={styles.deleteBtn}
        onClick={e => { e.stopPropagation(); onDelete(chat.id) }}
        aria-label={`Eliminar "${chat.title}"`}
        tabIndex={-1}
      >
        <XIcon />
      </button>
    </div>
  )
}

function XIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <line x1="2" y1="2" x2="10" y2="10" />
      <line x1="10" y1="2" x2="2" y2="10" />
    </svg>
  )
}