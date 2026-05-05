import styles from './NewChatButton.module.css'

export default function NewChatButton({ onClick }) {
  return (
    <button className={styles.btn} onClick={onClick} aria-label="Nueva conversación">
      <PlusIcon />
      Nueva conversación
    </button>
  )
}

function PlusIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
      <line x1="7" y1="1" x2="7" y2="13" />
      <line x1="1" y1="7" x2="13" y2="7" />
    </svg>
  )
}