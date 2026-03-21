import { createApp } from 'vue'
import ArcoVue from '@arco-design/web-vue'
import ArcoVueIcon from '@arco-design/web-vue/es/icon'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import '@arco-design/web-vue/dist/arco.css'
import './styles/index.css'
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

// Restore permission store from localStorage on app startup.
// This works uniformly for both web and desktop (PyQt6) modes.
const permissionStore = usePermissionStore()
permissionStore.restore()

console.info('[App] Initialized (web + desktop unified)')
