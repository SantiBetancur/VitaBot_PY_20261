import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import fs from 'fs'
import path from 'path'

// Función para cargar variables de entorno desde .env
function loadEnv() {
  const envPath = path.resolve('.env')
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf-8')
    const envVars = {}
    envContent.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split('=')
      if (key && valueParts.length > 0) {
        const value = valueParts.join('=').trim()
        if (key.startsWith('VITE_')) {
          envVars[key] = value.replace(/^["']|["']$/g, '') // Remove quotes
        }
      }
    })
    return envVars
  }
  return {}
}

const envVars = loadEnv()

// Leer las variables de entorno
const ENVIRONMENT = envVars.VITE_ENVIRONMENT || 'development'
const BACKEND_URL = ENVIRONMENT === 'production'
  ? envVars.VITE_BACKEND_URL_PRODUCTION
  : envVars.VITE_BACKEND_URL_DEV

console.log(`🚀 Vite config - Environment: ${ENVIRONMENT}`)
console.log(`🔗 Backend URL: ${BACKEND_URL}`)
console.log(`📝 Loaded env vars:`, envVars)
// vite.config.js — solo sirve para dev
export default defineConfig({
  plugins: [react()],
  server: {
    port: 4800,
    proxy: {
      '/server': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})