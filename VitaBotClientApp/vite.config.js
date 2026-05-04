import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
const APP_DOMAIN = 'https://vitabot-py-20261-kzkxzltd.onslate.com'
export default defineConfig({
  plugins: [react()],
  server: {
    port: 4800,
    strictPort: true,
    proxy: {
      '/server': {
        target: APP_DOMAIN,
        changeOrigin: true,
      },
    },
  },
})
