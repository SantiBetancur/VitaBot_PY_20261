import { useEffect, useState } from 'react'

const SDK_URL = 'https://static.zohocdn.com/catalyst/sdk/js/4.5.0/catalystWebSDK.js'
const INIT_URL = '/__catalyst/sdk/init.js'

let sdkLoadPromise = null

const loadScript = (src) => {
  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[src=\"${src}\"]`)
    if (existingScript) {
      if (existingScript.getAttribute('data-loaded') === 'true') {
        resolve()
      } else {
        existingScript.addEventListener('load', () => resolve())
        existingScript.addEventListener('error', () => reject(new Error(`Failed to load script ${src}`)))
      }
      return
    }

    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.onload = () => {
      script.setAttribute('data-loaded', 'true')
      resolve()
    }
    script.onerror = () => reject(new Error(`Failed to load script ${src}`))
    document.head.appendChild(script)
  })
}

const loadCatalystSDK = async () => {
  await loadScript(SDK_URL)
  await loadScript(INIT_URL)

  if (!window.catalyst) {
    throw new Error('Catalyst SDK cargado, pero window.catalyst no está disponible.')
  }

  return window.catalyst
}

export const ensureCatalystSDK = () => {
  if (!sdkLoadPromise) {
    sdkLoadPromise = loadCatalystSDK()
  }

  return sdkLoadPromise
}

export const useCatalystSDK = () => {
  const [state, setState] = useState({ isReady: false, error: null, catalyst: null })

  useEffect(() => {
    let isMounted = true

    ensureCatalystSDK()
      .then((catalyst) => {
        if (!isMounted) return
        setState({ isReady: true, error: null, catalyst })
      })
      .catch((loadError) => {
        if (!isMounted) return
        setState({ isReady: false, error: loadError.message, catalyst: null })
      })

    return () => {
      isMounted = false
    }
  }, [])

  return state
}
