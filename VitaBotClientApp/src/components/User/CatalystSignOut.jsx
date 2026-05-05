import { useCatalystSDK } from '../../hooks/useCatalystSDK'

let APP_DOMAIN = null
if (import.meta.env.VITE_ENVIRONMENT === 'development') {
  APP_DOMAIN = import.meta.env.VITE_APP_DOMAIN_DEV
} else {
  APP_DOMAIN = import.meta.env.VITE_APP_DOMAIN_PRODUCTION
}
const REDIRECT_URL = `${APP_DOMAIN}/`

const CatalystSignOut = ({ onSignOut }) => {
  const { isReady, catalyst } = useCatalystSDK()

  const handleSignOut = () => {
    if (!isReady || !catalyst) {
      console.warn('Catalyst SDK aún no está listo.')
      return
    }

    try {
      var redirectURL = REDIRECT_URL
      var auth = catalyst.auth
      auth.signOut(redirectURL)
      onSignOut && onSignOut()
    } catch (err) {
      console.error('Error al cerrar sesión:', err)
    }
  }

  return { handleSignOut, isReady }
}

export default CatalystSignOut