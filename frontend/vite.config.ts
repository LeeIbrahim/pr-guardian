import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // Port 3000 is used because Caddy proxies from 5173 -> 3000
    port: 3000, 
    strictPort: true,
    host: 'localhost',
    hmr: {
      protocol: 'wss',
      host: 'localhost',
      clientPort: 5173,
    },
  },
});