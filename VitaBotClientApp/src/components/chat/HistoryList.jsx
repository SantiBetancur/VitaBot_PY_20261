import HistoryItem from './HistoryItem'
import HistoryItemSkeleton from './HistoryItemSkeleton'
import { useChatContext } from '../../context/Chatcontext'
import styles from './HistoryList.module.css'

export default function HistoryList({ chats, activeChatId, onSelect, onDelete }) {
  const { isLoadingHistory } = useChatContext()

  if (isLoadingHistory) {
    return (
      <div className={styles.list} role="list" aria-label="Cargando historial de conversaciones">
        {Array.from({ length: 4 }).map((_, i) => (
          <HistoryItemSkeleton key={`skeleton-${i}`} />
        ))}
      </div>
    )
  }

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