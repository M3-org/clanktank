import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env from project root (3 levels up)
  const projectRoot = resolve(__dirname, '../../../')
  const env = loadEnv(mode, projectRoot, '');
  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
        }
      }
    },
    envDir: projectRoot // Tell Vite where to find .env files
  }
})