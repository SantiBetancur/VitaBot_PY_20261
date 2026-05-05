import styles from './TypingIndicator.module.css'

export default function TypingIndicator() {
  return (
    <div className={styles.wrapper} aria-label="La IA está escribiendo" role="status">
      <div className={styles.avatar} aria-hidden>AI</div>
      <div className={styles.bubble}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
    </div>
  )
}