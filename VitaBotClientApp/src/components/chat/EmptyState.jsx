import styles from './EmptyState.module.css'
import logo from '../../assets/images/logo2.png'

const SUGGESTIONS = [
  '¿Cómo convertir un string a date-time en Deluge?',
  'Ejemplo de función para calcular días entre dos fechas en Deluge',
  '¿Cómo consumir una API externa usando invokeUrl en Deluge?',
  '¿Cómo manejar errores en funciones de Deluge?',
  'Script para crear o actualizar registros en Zoho CRM con Deluge',
  '¿Cómo autenticar requests con OAuth en Deluge?',
  '¿Cómo manejar respuestas JSON anidadas y extraer valores específicos en Deluge?',
]

export default function EmptyState({ onSuggestion }) {
  return (
    <div className={styles.container} role="main">
      <div>
        <img className={styles.logo} src={logo} alt="LogoVT" />
      </div>
      <h2 className={styles.title}>¿En qué puedo ayudarte?</h2>
      <p className={styles.subtitle}>
        Escribe un mensaje o elige una sugerencia para comenzar.
      </p>
      <hr />
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