import TopBar from './TopBar'
import MessageList from './MessageList'
import InputArea from '../InputArea/InputArea'
import { useChatContext } from '../../context/Chatcontext'
import { useChat } from '../../hooks/useChat'
import styles from './ChatArea.module.css'

export default function ChatArea() {
  const { getActiveChat, state } = useChatContext()
  const { sendMessage, isTyping } = useChat()

  const activeChat = getActiveChat()
  const title = activeChat?.title ?? 'Nueva conversación'
  const messages = activeChat?.messages ?? []

  return (
    <div className={styles.area}>
      <TopBar title={title} />
      <MessageList
        messages={messages}
        isTyping={isTyping}
        onSuggestion={sendMessage}
      />
      <InputArea onSend={sendMessage} disabled={isTyping} />
    </div>
  )
}