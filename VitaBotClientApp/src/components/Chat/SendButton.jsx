import styles from './SendButton.module.css'

export default function SendButton({ onClick, disabled }) {
  return (
    <button
      className={styles.btn}
      onClick={onClick}
      disabled={disabled}
      aria-label="Enviar mensaje"
    >
      <SendIcon />
    </button>
  )
}

function SendIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
         stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <path d="M2 12L12 7 2 2v4l7 1-7 1z" strokeLinejoin="round" />
    </svg>
  )
}