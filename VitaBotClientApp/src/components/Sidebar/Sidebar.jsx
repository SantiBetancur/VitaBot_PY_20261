import { useState } from 'react'
import NewChatButton from '../Chat/NewchatButton'
import HistoryList from '../Chat/HistoryList'
import ProfileButton from '../User/ProfileButton'
import { useChatHistory } from '../../hooks/useChatHistory'
import styles from './Sidebar.module.css'
import logo from '../../assets/images/logoVT2.png'

export default function Sidebar() {
  const { chats, activeChatId, createChat, deleteChat, selectChat } = useChatHistory()
  const [registerSignal, setRegisterSignal] = useState(0)

  return (
    <aside className={styles.sidebar} aria-label="Panel lateral">
      <div className={styles.header}>
        <div className={styles.logo} aria-hidden="true">
          <img src={logo} alt="Vita Bot" />
        </div>
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
        <ProfileButton openRegisterSignal={registerSignal} />
      
        <hr />
        <div className={styles.modelInfo}>
          modelo · Haiku-4.5
        </div>

      </div>
    </aside>
  )
}