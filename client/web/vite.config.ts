import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  // 根据环境选择API基础地址
  const getApiBaseUrl = (): string => {
    switch (mode) {
      case 'production':
        return env.VITE_API_BASE_URL_PRODUCTION || 'http://106.15.32.246:8000'
      case 'test':
        return env.VITE_API_BASE_URL_TEST || 'http://localhost:8000'
      case 'development':
      default:
        return env.VITE_API_BASE_URL_DEVELOPMENT || 'http://localhost:8000'
    }
  }
  
  const apiBaseUrl = getApiBaseUrl()
  
  console.log(`🚀 Vite Config - Mode: ${mode}`)
  console.log(`🌐 API Base URL: ${apiBaseUrl}`)
  console.log(`📊 Environment: ${env.VITE_ENV || 'development'}`)

  return {
    plugins: [vue()],

    // Use relative base so assets load correctly from file:// (PyQt6 WebEngine)
    base: './',

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },

    server: {
      host: true,
      port: 5173,
      open: false,
      cors: true,
      // Dev proxy: forwards /api requests to the backend server
      // In production builds this has no effect — axios calls apiBaseUrl directly
      proxy: {
        '/api': {
          target: apiBaseUrl,
          changeOrigin: true,
        },
      },
    },

    build: {
      target: 'chrome100',
      outDir: 'dist',
      assetsDir: 'assets',
      minify: 'esbuild',
      sourcemap: false,
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          chunkFileNames:  'assets/js/[name]-[hash].js',
          entryFileNames:  'assets/js/[name]-[hash].js',
          assetFileNames:  'assets/[ext]/[name]-[hash].[ext]',
          manualChunks: {
            'vendor-vue':   ['vue', 'vue-router', 'pinia'],
            'vendor-arco':  ['@arco-design/web-vue'],
            'vendor-axios': ['axios'],
          },
        },
      },
    },

    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
        },
      },
    },
  }
})
