import styles from './Message.module.css'
import ReactMarkdown from 'react-markdown'

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.ai}`}>
      {/*
      <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}
           aria-hidden>
        {isUser ? 'Tú' : 'AI'}
      </div>
      */}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.error : ''}`}>
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        )}
      </div>
    </div>
  )
}