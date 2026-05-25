import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,          // CRITICAL FIX
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',   // Docker service name
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
      },
    },
  },
})
