import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/files': 'http://134.157.105.72:8000',
      '/auth': 'http://134.157.105.72:8000',
      '/pdf_manual': 'http://134.157.105.72:8000',
    }
  }
});