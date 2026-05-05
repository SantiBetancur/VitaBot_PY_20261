import React, { useEffect, useState } from 'react'
import styles from './CatalystRegistration.module.css'
import { useCatalystSDK } from '../../hooks/useCatalystSDK'

const CatalystRegistration = ({ onRegistered, onCancel }) => {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const { isReady, error: sdkError } = useCatalystSDK()
  let APP_DOMAIN = null
  if (import.meta.env.VITE_ENVIRONMENT === 'development') {
    APP_DOMAIN = import.meta.env.VITE_APP_DOMAIN_DEV
  } else {
    APP_DOMAIN = import.meta.env.VITE_APP_DOMAIN_PRODUCTION
  }
  useEffect(() => {
    if (sdkError) {
      setError(sdkError)
    }
  }, [sdkError])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus(null)
    setError(null)

    if (!firstName || !lastName || !email) {
      setError('Por favor completa todos los campos de registro.')
      return
    }

    if (!isReady) {
      setError('Catalyst SDK aún no está listo. Espera un momento.')
      return
    }

    if (!window.catalyst || !window.catalyst.auth) {
      setError('Catalyst auth no está disponible. Asegúrate de que el init script se cargue correctamente.')
      return
    }

   

    const signupData = {
      first_name: firstName,
      last_name: lastName,
      email_id: email,
      platform_type: 'web',
      redirect_url: `${APP_DOMAIN}/`
    }

    try {
      setIsSubmitting(true)
      const auth = window.catalyst.auth
      const signupPromise = auth.signUp(signupData)
      const response = await signupPromise
      
      const userDetails = response.content || response
      setStatus(userDetails)
      onRegistered && onRegistered(userDetails)
    } catch (submitError) {
      console.error('Error registrando usuario:', submitError)
      setError(submitError?.message || 'Error al crear el usuario.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={styles.registrationContainer}>
      <div className={styles.registrationHeader}>
        <h2 className={styles.registrationTitle}>Regístrate en Vita<span>Bot</span></h2>
       
      </div>

      {!isReady && !error && (
        <div className={styles.loadingText}>Cargando Catalyst... Por favor espera.</div>
      )}

      {error && (
        <div className={`${styles.statusMessage} ${styles.error}`}>
          {error}
        </div>
      )}

      {status && (
        <div className={`${styles.statusMessage} ${styles.success}`}>
          <strong>Registro completado:</strong>
          <pre style={{ overflowX: 'auto', margin: '8px 0 0' }}>
            {JSON.stringify(status, null, 2)}
          </pre>
        </div>
      )}

      <form className={styles.registrationForm} onSubmit={handleSubmit}>
        <div className={styles.fieldGroup}>
          <label htmlFor="firstName">Nombre</label>
          <input
            id="firstName"
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Dannie"
          />
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="lastName">Apellido</label>
          <input
            id="lastName"
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Boyle"
          />
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="email">Correo electrónico</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="p.boyle@zylker.com"
          />
        </div>

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onCancel}
          >
            Volver
          </button>
          <button
            type="submit"
            className={styles.primaryButton}
            disabled={!isReady || isSubmitting}
          >
            {isSubmitting ? 'Registrando...' : 'Crear usuario'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default CatalystRegistration
