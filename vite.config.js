import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const port = parseInt(env.VITE_PORT || env.PORT || '5173', 10);
  const host = env.VITE_HOST === 'true' ? true : (env.VITE_HOST || '0.0.0.0');

  return {
    plugins: [react()],
    server: {
      host,
      port,
    },
    preview: {
      host,
      port,
    },
  };
})

