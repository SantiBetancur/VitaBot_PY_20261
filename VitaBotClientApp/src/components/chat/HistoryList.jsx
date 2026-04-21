import HistoryItem from './HistoryItem'
import styles from './HistoryList.module.css'

export default function HistoryList({ chats, activeChatId, onSelect, onDelete }) {
  if (chats.length === 0) {
    return <p className={styles.empty}>Sin conversaciones aún.</p>
  }

  return (
    <div className={styles.list} role="list" aria-label="Historial de conversaciones">
      {chats.map(chat => (
        <HistoryItem
          key={chat.id}
          chat={chat}
          isActive={chat.id === activeChatId}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}