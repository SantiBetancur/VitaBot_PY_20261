import { useState } from 'react'
import styles from './ProfileButton.module.css'

export default function ProfileButton() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const handleClick = () => {
    if (isLoggedIn) {
      // Cerrar sesión
      setIsLoggedIn(false)
      alert('Sesión cerrada')
    } else {
      // Iniciar sesión (simulado)
      setIsLoggedIn(true)
      alert('Sesión iniciada')
    }
  }

  return (
    <button
      className={styles.profileButton}
      onClick={handleClick}
      title={isLoggedIn ? 'Cerrar sesión' : 'Iniciar sesión'}
      aria-label={isLoggedIn ? 'Cerrar sesión' : 'Iniciar sesión'}
    >
      <span className={styles.icon}>
        {isLoggedIn ? '👤' : '🔒'}
      </span>
    </button>
  )
}