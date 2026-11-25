import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In development the app calls /api on the Vite server; forward it to the
    // FastAPI backend, which serves the same routes under /api.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
