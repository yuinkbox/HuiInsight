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
import { auth } from '@/utils/auth'

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
const permissionStore = usePermissionStore()

/**
 * Apply a token_info dict (from login response or bridge signal) to
 * localStorage so that axios interceptors and route guards work.
 */
function _applyTokenInfo(tokenInfo: any): void {
  try {
    const token: string = tokenInfo.access_token ?? ''
    const user = tokenInfo.user ?? {
      username: tokenInfo.username ?? tokenInfo.sub ?? '',
      full_name: tokenInfo.full_name ?? '',
      role: tokenInfo.role ?? '',
      is_superuser: tokenInfo.is_superuser ?? false,
    }
    if (!token) {
      console.warn('[App] tokenInfo has no access_token field:', tokenInfo)
      return
    }
    auth.saveLoginData(token, user)
    permissionStore.bootstrap({
      role: tokenInfo.role ?? user.role ?? '',
      permissions: tokenInfo.permissions ?? [],
      role_meta: tokenInfo.role_meta ?? {
        label: tokenInfo.role ?? '',
        color: 'gray',
        dashboard_view: 'auditor',
      },
    })
    console.info('[App] Token applied: user=%s role=%s', user.username, tokenInfo.role)

    // Navigate to dashboard if currently on login page
    const current = router.currentRoute.value
    if (current.name === 'Login' || current.path === '/' || current.path === '/login') {
      router.push({ name: 'Dashboard' })
    }
  } catch (err) {
    console.error('[App] _applyTokenInfo error:', err)
  }
}

if (isDesktopMode()) {
  // Desktop (PyQt6 WebEngine) mode:
  // 1. Connect to QWebChannel bridge.
  // 2. Read the token that Python already injected (login happened in native window).
  // 3. Subscribe to tokenInfoChanged for future updates (e.g. token refresh).
  getBridge().then(async (bridge) => {
    if (!bridge) {
      console.warn('[App] QWebChannel bridge unavailable.')
      return
    }
    console.info('[App] QWebChannel bridge ready.')

    // Subscribe to future token updates
    bridge.tokenInfoChanged.connect((raw: string) => {
      try {
        const info = JSON.parse(raw)
        _applyTokenInfo(info)
      } catch (err) {
        console.warn('[App] tokenInfoChanged parse error:', err)
      }
    })

    // Read token that was already set before the page loaded
    try {
      const raw = await bridge.getTokenInfo()
      if (raw && raw !== '{}') {
        const info = JSON.parse(raw)
        _applyTokenInfo(info)
      } else {
        console.warn('[App] Bridge has no token yet - waiting for tokenInfoChanged signal.')
      }
    } catch (err) {
      console.warn('[App] getTokenInfo error:', err)
    }
  })
} else {
  // Browser / web mode: restore from localStorage
  console.info('[App] Running in browser/web mode.')
  permissionStore.restore()
}
