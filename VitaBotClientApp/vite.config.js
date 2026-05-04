import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
const BACKEND_URL = 'http://localhost:3000'
export default defineConfig({
  plugins: [react()],
  server: {
    port: 4800,
    strictPort: true,
    proxy: {
      '/server': {
        target: BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
})
