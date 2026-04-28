import { useState } from 'react'
import styles from './ProfileButton.module.css'
import CatalystLogin from './CatalystLogin'

export default function ProfileButton() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)

  const handleClick = () => {
    if (isLoggedIn) {
      // Cerrar sesión
      setIsLoggedIn(false)
      alert('Sesión cerrada')
    } else {
      // Mostrar modal de login
      setShowLoginModal(true)
    }
  }

  const handleLoginSuccess = () => {
    setIsLoggedIn(true)
    setShowLoginModal(false)
    console.log('Usuario autenticado exitosamente')
  }

  const handleLoginError = (error) => {
    console.error('Error en la autenticación:', error)
    // El modal permanece abierto para que el usuario pueda intentar de nuevo
  }

  const handleCloseModal = () => {
    setShowLoginModal(false)
  }

  return (
    <>
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

      {showLoginModal && (
        <div className={styles.loginModal}>
          <div className={styles.loginOverlay} onClick={handleCloseModal}></div>
          <div className={styles.loginContent}>
            <button className={styles.closeButton} onClick={handleCloseModal}>
              ×
            </button>
            <CatalystLogin
              onSuccess={handleLoginSuccess}
              onError={handleLoginError}
            />
          </div>
        </div>
      )}
    </>
  )
}