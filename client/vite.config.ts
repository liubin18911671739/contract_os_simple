import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['lucide-react', 'recharts'],
          'state-vendor': ['zustand'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Increase timeout for long-running requests (LLM analysis can take time)
        timeout: 600000, // 10 minutes
        // Disable keep-alive to prevent ECONNRESET errors
        proxyTimeout: 600000,
        // Rewrite headers to prevent connection issues
        rewrite: (path) => path,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            // Force close connection to prevent keep-alive issues
            proxyReq.setHeader('Connection', 'close');
          });
          proxy.on('error', (err, _req, res) => {
            // Handle proxy errors gracefully
            if (!res.writableEnded) {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Proxy Error', message: err.message }));
            }
          });
        },
      },
    },
  },
});
