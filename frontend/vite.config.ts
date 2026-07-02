import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    hmr: {
      clientPort: 80,
    },
    proxy: {
      // 将 /api/shop/* 代理到 Nginx (:80)
      '/api/shop': {
        target: 'http://localhost:80',
        changeOrigin: true,
      },
      // 将 /api/ai/* 代理到 AI 服务
      '/api/ai': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
})
