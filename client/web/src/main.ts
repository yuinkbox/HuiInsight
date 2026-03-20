import { createApp } from 'vue'
import ArcoVue from '@arco-design/web-vue'
import ArcoVueIcon from '@arco-design/web-vue/es/icon'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@arco-design/web-vue/dist/arco.css'
import './styles/index.css'
import { isDesktopMode, getBridge } from '@/bridge/qt_channel'
import { usePermissionStore } from '@/stores/permission'

// Enable dark theme
document.body.setAttribute('arco-theme', 'dark')

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ArcoVue)
app.use(ArcoVueIcon)
app.mount('#app')

// Restore permission store from localStorage / API on every page load.
// This ensures the Pinia store is hydrated even after a hard refresh,
// so route guards and v-if directives work correctly before any user action.
const permissionStore = usePermissionStore()
permissionStore.restore()

// In desktop (PyQt6 WebEngine) mode, initialise the QWebChannel bridge.
if (isDesktopMode()) {
  getBridge().then((bridge) => {
    if (bridge) {
      console.info('[App] QWebChannel bridge ready.')
    } else {
      console.warn('[App] QWebChannel bridge unavailable.')
    }
  })
} else {
  console.info('[App] Running in browser/web mode.')
}
