import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND_URL = process.env.VITE_BACKEND_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,          // CRITICAL FIX
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
      },
      '/ws': {
        target: BACKEND_URL.replace(/^http/, 'ws'),
        ws: true,
      },
    },
  },
})
