import styles from './Message.module.css'

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.ai}`}>
      <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarAi}`}
           aria-hidden>
        {isUser ? 'Tú' : 'AI'}
      </div>
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAi} ${message.isError ? styles.error : ''}`}>
        {message.content}
      </div>
    </div>
  )
}