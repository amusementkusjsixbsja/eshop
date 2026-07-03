import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Windows + Docker bind-mount 下 inotify 文件事件不传递，
    // 必须开启轮询，否则改了 src 里的文件 Vite 不会热更新。
    watch: {
      usePolling: true,
      interval: 300,
    },
    hmr: {
      clientPort: 90,
    },
    proxy: {
      // 将 /api/shop/* 代理到 Nginx (:90)
      '/api/shop': {
        target: 'http://localhost:90',
        changeOrigin: true,
      },
      // 将 /api/ai/* 代理到 AI 服务（直接连 Docker 暴露端口，不走 Nginx）
      '/api/ai': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
})
