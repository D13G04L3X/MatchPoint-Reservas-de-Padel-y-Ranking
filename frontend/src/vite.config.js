import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/bookings': 'http://localhost',
      '/courts': 'http://localhost',
      '/penalty': 'http://localhost',
      '/health': 'http://localhost',
    },
  },
})
