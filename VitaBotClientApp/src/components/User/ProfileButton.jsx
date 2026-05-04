import { useState, useEffect, useRef } from 'react'
import styles from './ProfileButton.module.css'
import CatalystLogin from './CatalystLogin'
import CatalystRegistration from './CatalystRegistration'
import UserProfile from './UserProfile'
import { useCatalystSDK } from '../../hooks/useCatalystSDK'

const APP_DOMAIN = import.meta.env.VITE_APP_DOMAIN
const REDIRECT_URL = `${APP_DOMAIN}/`

export default function ProfileButton({ openRegisterSignal = 0 }) {
  const [user, setUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [showProfilePanel, setShowProfilePanel] = useState(false)
  const profilePanelRef = useRef(null)

  const { isReady, catalyst } = useCatalystSDK()
  const isLoggedIn = !!user

  // ── Check active session on SDK ready ──────────────────────────────
  useEffect(() => {
    if (!isReady || !catalyst) return

    var userManagement = catalyst.userManagement
    userManagement
      .getCurrentProjectUser()
      .then((response) => {
        const userData = response.content
        if (userData && userData.user_id) {
          setUser(userData)
        }
      })
      .catch(() => {
        // No active session — show login/register normally
        setUser(null)
      })
      .finally(() => {
        setAuthChecked(true)
      })
  }, [isReady, catalyst])

  // ── Open register tab from external signal ─────────────────────────
  useEffect(() => {
    if (openRegisterSignal > 0 && authChecked && !isLoggedIn) {
      setShowLoginModal(true)
      setShowRegister(true)
    }
  }, [openRegisterSignal, authChecked, isLoggedIn])

  // ── Close profile panel on outside click ───────────────────────────
  useEffect(() => {
    if (!showProfilePanel) return
    const handleOutside = (e) => {
      if (profilePanelRef.current && !profilePanelRef.current.contains(e.target)) {
        setShowProfilePanel(false)
      }
    }
    document.addEventListener('mousedown', handleOutside)
    return () => document.removeEventListener('mousedown', handleOutside)
  }, [showProfilePanel])

  const handleClick = () => {
    if (isLoggedIn) {
      setShowProfilePanel((prev) => !prev)
    } else {
      setShowLoginModal(true)
      setShowRegister(false)
    }
  }

  // Called by CatalystLogin after redirect back to the app
  const handleLoginSuccess = () => {
    if (!isReady || !catalyst) return
    var userManagement = catalyst.userManagement
    userManagement
      .getCurrentProjectUser()
      .then((response) => {
        const userData = response.content
        if (userData && userData.user_id) {
          setUser(userData)
          setShowLoginModal(false)
        }
      })
      .catch((err) => {
        console.error('Error fetching user after login:', err)
      })
  }

  const handleLoginError = (error) => {
    console.error('Error en la autenticación:', error)
  }

  const handleRegisterSuccess = (userDetails) => {
    console.log('Usuario registrado:', userDetails)
    setShowLoginModal(false)
    setShowRegister(false)
    alert('Usuario registrado correctamente. Revisa el correo para confirmar la invitación.')
  }

  const handleCloseModal = () => {
    setShowLoginModal(false)
    setShowRegister(false)
  }

  const handleSignOut = () => {
    if (!isReady || !catalyst) return
    var redirectURL = REDIRECT_URL
    var auth = catalyst.auth
    auth.signOut(redirectURL)
    setUser(null)
    setShowProfilePanel(false)
  }

  // ── Avatar: initials when logged in, lock icon otherwise ───────────
  const avatarContent = isLoggedIn
    ? `${(user.first_name || '?')[0]}${(user.last_name || '')[0] || ''}`.toUpperCase()
    : '🤖'

  // Don't render anything until we know the auth state
  if (!authChecked) return null

  return (
    <>
      <div className={styles.profileWrapper} ref={profilePanelRef}>
        <button
          className={`${styles.profileButton} ${isLoggedIn ? styles.loggedIn : ''}`}
          onClick={handleClick}
          title={isLoggedIn ? `${user.first_name} ${user.last_name}` : 'Iniciar sesión'}
          aria-label={isLoggedIn ? 'Ver perfil' : 'Iniciar sesión'}
        >
          <span className={styles.icon}>{avatarContent}</span>
        </button>

        {showProfilePanel && isLoggedIn && (
          <div className={styles.profilePanel}>
            <UserProfile user={user} onSignOut={handleSignOut} />
          </div>
        )}
      </div>

      {showLoginModal && !isLoggedIn && (
        <div className={styles.loginModal}>
          <div className={styles.loginOverlay} onClick={handleCloseModal} />
          <div className={styles.loginContent}>
            <button className={styles.closeButton} onClick={handleCloseModal}>×</button>
            <div className={styles.modalTabs}>
              <button
                className={`${styles.tabButton} ${!showRegister ? styles.activeTab : ''}`}
                onClick={() => setShowRegister(false)}
              >
                Iniciar sesión
              </button>
              <button
                className={`${styles.tabButton} ${showRegister ? styles.activeTab : ''}`}
                onClick={() => setShowRegister(true)}
              >
                Registrarse
              </button>
            </div>
            {showRegister ? (
              <CatalystRegistration
                onRegistered={handleRegisterSuccess}
                onCancel={handleCloseModal}
              />
            ) : (
              <CatalystLogin
                onSuccess={handleLoginSuccess}
                onError={handleLoginError}
              />
            )}
          </div>
        </div>
      )}
    </>
  )
}