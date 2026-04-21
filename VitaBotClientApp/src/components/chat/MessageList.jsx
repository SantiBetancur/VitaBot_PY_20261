import { useEffect, useRef } from 'react'
import Message from './Message'
import TypingIndicator from './TypingIndicator'
import EmptyState from './EmptyState'
import styles from './MessageList.module.css'

export default function MessageList({ messages, isTyping, onSuggestion }) {
  const bottomRef = useRef(null)

  // Auto-scroll when new messages arrive or typing starts
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const isEmpty = messages.length === 0 && !isTyping

  return (
    <div className={styles.area} role="log" aria-live="polite" aria-label="Conversación">
      {isEmpty ? (
        <EmptyState onSuggestion={onSuggestion} />
      ) : (
        <div className={styles.inner}>
          {messages.map(msg => (
            <Message key={msg.id} message={msg} />
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={bottomRef} aria-hidden />
        </div>
      )}
    </div>
  )
}