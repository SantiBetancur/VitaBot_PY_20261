import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4800,
    strictPort: true,
    proxy: {
      '/server': {
        target: 'http://localhost:3002',
        changeOrigin: true,
      },
    },
  },
})
