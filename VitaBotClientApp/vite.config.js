import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
const APP_DOMAIN = process.env.APP_DOMAIN || 'http://localhost:3001'
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/__catalyst': {
        target: `${APP_DOMAIN}`,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
