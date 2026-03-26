/**
 * 统一认证管理工具
 * 确保 Token 存储与登录记忆逻辑一致。
 */

export const TOKEN_KEY = 'ahdunyi_access_token'
export const USER_INFO_KEY = 'ahdunyi_user_info'
export const LAST_USERNAME_KEY = 'ahdunyi_last_username'
export const REMEMBERED_ACCOUNTS_KEY = 'ahdunyi_remembered_accounts'

export interface RememberedAccount {
  username: string
  password: string
  updatedAt: number
}

function normalizeUsername(username: string): string {
  return String(username || '').trim()
}

function readRememberedAccounts(): RememberedAccount[] {
  try {
    const raw = localStorage.getItem(REMEMBERED_ACCOUNTS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []

    return parsed
      .filter((item) => item && typeof item.username === 'string' && typeof item.password === 'string')
      .map((item) => ({
        username: normalizeUsername(item.username),
        password: String(item.password),
        updatedAt: Number(item.updatedAt || Date.now()),
      }))
      .filter((item) => item.username.length > 0)
      .sort((a, b) => b.updatedAt - a.updatedAt)
  } catch {
    return []
  }
}

function writeRememberedAccounts(accounts: RememberedAccount[]): void {
  localStorage.setItem(REMEMBERED_ACCOUNTS_KEY, JSON.stringify(accounts))
}

export const auth = {
  saveLoginData: (accessToken: string, userInfo: any, rememberMe = false, lastUsername?: string): boolean => {
    try {
      localStorage.setItem(TOKEN_KEY, accessToken)
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))

      const normalized = normalizeUsername(lastUsername || '')
      if (rememberMe && normalized) {
        localStorage.setItem(LAST_USERNAME_KEY, normalized)
      } else {
        localStorage.removeItem(LAST_USERNAME_KEY)
      }
      return true
    } catch (error) {
      console.error('保存登录信息失败:', error)
      return false
    }
  },

  saveRememberedPassword: (username: string, password: string): void => {
    const normalized = normalizeUsername(username)
    if (!normalized) return

    const accounts = readRememberedAccounts().filter((item) => item.username !== normalized)
    accounts.unshift({ username: normalized, password, updatedAt: Date.now() })
    writeRememberedAccounts(accounts)
  },

  removeRememberedPassword: (username: string): void => {
    const normalized = normalizeUsername(username)
    if (!normalized) return

    const accounts = readRememberedAccounts().filter((item) => item.username !== normalized)
    writeRememberedAccounts(accounts)

  },



  migrateRememberedUsername: (oldUsername: string, newUsername: string): void => {
    const oldNormalized = normalizeUsername(oldUsername)
    const newNormalized = normalizeUsername(newUsername)
    if (!oldNormalized || !newNormalized || oldNormalized === newNormalized) return

    const accounts = readRememberedAccounts()
    const oldRecord = accounts.find((item) => item.username === oldNormalized)
    const merged = accounts.filter((item) => item.username !== oldNormalized && item.username !== newNormalized)

    if (oldRecord) {
      merged.unshift({
        username: newNormalized,
        password: oldRecord.password,
        updatedAt: Date.now(),
      })
      writeRememberedAccounts(merged)
    }

    if (localStorage.getItem(LAST_USERNAME_KEY) === oldNormalized) {
      localStorage.setItem(LAST_USERNAME_KEY, newNormalized)
    }
  },

  getRememberedAccounts: (): RememberedAccount[] => readRememberedAccounts(),

  getRememberedPassword: (username: string): string => {
    const normalized = normalizeUsername(username)
    if (!normalized) return ''

    const found = readRememberedAccounts().find((item) => item.username === normalized)
    return found?.password || ''
  },

  getToken: (): string | null => localStorage.getItem(TOKEN_KEY),

  getUserInfo: (): any | null => {
    try {
      const userInfo = localStorage.getItem(USER_INFO_KEY)
      return userInfo ? JSON.parse(userInfo) : null
    } catch {
      return null
    }
  },

  getLastUsername: (): string | null => localStorage.getItem(LAST_USERNAME_KEY),

  clearAuthSession: (): void => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_INFO_KEY)
    localStorage.removeItem('ahdunyi_permissions')

    // 兼容清理旧键
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('token')
  },

  clearLoginData: (): void => {
    auth.clearAuthSession()
    localStorage.removeItem(LAST_USERNAME_KEY)
  },

  isLoggedIn: (): boolean => {
    const token = auth.getToken()
    const user = auth.getUserInfo()
    return !!(token && user && user.username && user.id)
  },

  getBearerToken: (): string => {
    const token = auth.getToken()
    return token ? `Bearer ${token}` : ''
  },

  validateToken: (token: string): boolean => {
    if (!token || token.length < 10) return false
    return true
  },
}

export default auth
