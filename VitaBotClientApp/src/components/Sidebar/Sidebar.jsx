import NewChatButton from '../Chat/NewchatButton'
import HistoryList from '../Chat/HistoryList'
import { useChatHistory } from '../../hooks/useChatHistory'
import styles from './Sidebar.module.css'

export default function Sidebar() {
  const { chats, activeChatId, createChat, deleteChat, selectChat } = useChatHistory()

  return (
    <aside className={styles.sidebar} aria-label="Panel lateral">
      <div className={styles.header}>
        <span className={styles.logo}>Vita Bot</span>
        <NewChatButton onClick={createChat} />
      </div>

      <p className={styles.sectionLabel}>Historial</p>

      <HistoryList
        chats={chats}
        activeChatId={activeChatId}
        onSelect={selectChat}
        onDelete={deleteChat}
      />

      <div className={styles.footer}>
        modelo · spark-2.1
      </div>
    </aside>
  )
}