import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['mapbox-gl'],
    esbuildOptions: {
      target: 'es2020'
    }
  },
  server: {
    port: 3002,
    host: true,
    // Limit concurrent HMR file requests to prevent ERR_INSUFFICIENT_RESOURCES
    fs: {
      strict: false,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8003',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    // Split large chunks to reduce memory pressure
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts'],
          'flow-vendor': ['reactflow'],
          'ui-vendor': ['lucide-react', 'framer-motion'],
        }
      }
    }
  },
  // Reduce memory usage during dev by limiting concurrent transforms
  worker: {
    format: 'es'
  }
})
