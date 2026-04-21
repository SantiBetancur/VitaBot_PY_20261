import styles from './EmptyState.module.css'

const SUGGESTIONS = [
  '¿Cómo funciona la IA?',
  'Escríbeme un poema breve',
  'Explica qué es React',
  'Dame ideas para un proyecto',
  'Resúmeme un concepto complejo',
  'Ayúdame a escribir un correo',
]

export default function EmptyState({ onSuggestion }) {
  return (
    <div className={styles.container} role="main">
      <div className={styles.icon} aria-hidden>
        <SparkIcon />
      </div>
      <h2 className={styles.title}>¿En qué puedo ayudarte?</h2>
      <p className={styles.subtitle}>
        Escribe un mensaje o elige una sugerencia para comenzar.
      </p>
      <div className={styles.chips} role="list" aria-label="Sugerencias">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            className={styles.chip}
            onClick={() => onSuggestion(s)}
            role="listitem"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

function SparkIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none"
         stroke="currentColor" strokeWidth="1.4" aria-hidden>
      <circle cx="10" cy="10" r="8" />
      <path d="M10 6v4l3 2" strokeLinecap="round" />
    </svg>
  )
}