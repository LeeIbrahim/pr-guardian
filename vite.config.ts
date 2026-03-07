import react from '@vitejs/plugin-react';
import fs from 'fs';

export default {
  plugins: [react()],
  server: {
    port: 5173,
    https: {
      key: fs.readFileSync('./key.pem'),
      cert: fs.readFileSync('./cert.pem'),
    },
    host: 'localhost',
  },
};