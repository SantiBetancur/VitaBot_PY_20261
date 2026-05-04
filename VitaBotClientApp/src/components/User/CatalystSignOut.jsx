import { useCatalystSDK } from '../../hooks/useCatalystSDK'

const APP_DOMAIN = "https://vitabotclientapp-ycwjmrpr.onslate.com"
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