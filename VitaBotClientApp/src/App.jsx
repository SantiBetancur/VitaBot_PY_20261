import { ChatProvider } from './context/Chatcontext'
import Sidebar from './components/Sidebar/Sidebar'
import ChatArea from './components/Chat/ChatArea'
import styles from './App.module.css'

export default function App() {
  return (
    <ChatProvider>
      <div className={styles.layout}>
        <Sidebar />
        <ChatArea />
      </div>
    </ChatProvider>
  )
}