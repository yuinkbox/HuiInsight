<template>
  <div class="login-page">
    <div class="window-chrome">
      <div class="chrome-left">
        <span class="dot red" /><span class="dot yellow" /><span class="dot green" />
      </div>
      <span class="chrome-title">HuiInsight Secure Sign-in</span>
      <span class="chrome-env">TEST</span>
    </div>
    <div class="bg">
      <div class="c c1" /><div class="c c2" /><div class="c c3" />
    </div>

    <a-card
      class="login-card"
      :bordered="false"
    >
      <template #cover>
        <div class="card-header">
          <div class="logo">
            <icon-computer :size="32" /><span class="logo-text">AHDUNYI</span>
          </div>
          <a-typography-title
            :level="3"
            class="welcome-text"
          >
            徽鉴 HuiInsight
          </a-typography-title>
          <a-typography-text
            type="secondary"
            class="subtitle"
          >
            工作辛苦了，但也需要保持专注与严谨哦。
          </a-typography-text>
        </div>
      </template>

      <div class="login-form">
        <div class="form-item">
          <a-auto-complete
            v-model="username"
            :data="filteredAccountOptions"
            @focus="showAllHistoryAccounts"
            @search="handleUsernameSearch"
            @select="handleUsernameSelect"
          >
            <a-input
              v-model="username"
              placeholder="请输入用户名"
              size="large"
              allow-clear
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-auto-complete>
        </div>

        <div class="form-item">
          <a-input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            size="large"
            allow-clear
            @keyup.enter="handleLogin"
            @input="handlePasswordInput"
            @paste="handlePasswordPaste"
          >
            <template #prefix>
              <icon-lock />
            </template>
            <template #suffix>
              <a-button
                type="text"
                size="mini"
                class="pwd-toggle-btn"
                :disabled="isAutoFilledPassword"
                @click="showPassword = !showPassword"
              >
                <icon-eye v-if="!showPassword" /><icon-eye-invisible v-else />
              </a-button>
            </template>
          </a-input>
        </div>

        <Transition name="alert-slide">
          <div
            v-if="rememberedAccounts.length > 0"
            class="history-account-bar"
          >
            <a-typography-text
              type="secondary"
              class="history-label"
            >
              历史账号
            </a-typography-text>
            <div class="history-tags">
              <a-tag
                v-for="item in rememberedAccounts"
                :key="item.username"
                closable
                bordered
                class="history-tag"
                @mousedown.prevent="applyRememberedAccount(item.username)"
                @close="removeRememberedAccount(item.username)"
              >
                {{ item.username }}
              </a-tag>
            </div>
          </div>
        </Transition>

        <div class="form-item remember-item">
          <div class="remember-options">
            <a-checkbox v-model="rememberAccount">
              记住账号
            </a-checkbox><a-checkbox v-model="rememberPassword">
              记住密码
            </a-checkbox>
          </div>
          <a-link @click="showForgetPassword">
            忘记密码？
          </a-link>
        </div>

        <a-button
          type="primary"
          size="large"
          long
          :loading="loginLoading"
          :disabled="!canLogin"
          class="login-button"
          @click="handleLogin"
        >
          <template #icon>
            <icon-login v-if="!loginLoading" />
          </template>{{ loginLoading ? '登录中...' : '立即登录' }}
        </a-button>

        <Transition name="alert-slide">
          <div
            v-if="apiStatus"
            class="api-status"
          >
            <a-alert
              :type="apiStatus.type"
              :title="apiStatus.title"
              :content="apiStatus.content"
              show-icon
              closable
              @close="apiStatus = null"
            />
          </div>
        </Transition>
        <Transition name="alert-slide">
          <div
            v-if="!backendConnected"
            class="backend-status"
          >
            <a-alert
              type="warning"
              show-icon
            >
              <template #icon>
                <icon-wifi />
              </template>后端服务未连接<template #content>
                请确保后端服务正在运行 ({{ apiBaseUrl }}) <a-link @click="checkBackend">
                  点击重试
                </a-link>
              </template>
            </a-alert>
          </div>
        </Transition>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import api from '@/api'
import config from '@/config'
import { auth, type RememberedAccount } from '@/utils/auth'
import { usePermissionStore } from '@/stores/permission'

interface ApiStatus { type: 'success' | 'warning' | 'error' | 'info'; title: string; content: string }
const router = useRouter(); const route = useRoute(); const permissionStore = usePermissionStore()
const username = ref(''); const password = ref(''); const rememberAccount = ref(false); const rememberPassword = ref(false)
const showPassword = ref(false); const isAutoFilledPassword = ref(false); const isApplyingHistory = ref(false)
const loginLoading = ref(false); const backendConnected = ref(true); const rememberedAccounts = ref<RememberedAccount[]>([])
const accountQuery = ref(''); const apiStatus = ref<ApiStatus | null>(null); const apiBaseUrl = config.api.baseUrl

const canLogin = computed(() => username.value.trim().length > 0 && password.value.length >= 6)
const filteredAccountOptions = computed(() => {
  const q = accountQuery.value.trim().toLowerCase()
  return (q ? rememberedAccounts.value.filter((i) => i.username.toLowerCase().includes(q)) : rememberedAccounts.value).map((i) => i.username)
})
const clean = (t: string): string => t.replace(/[^a-zA-Z0-9_]/g, '')
const warnInvalid = () => { if (navigator.vibrate) navigator.vibrate([50, 30, 50]); Message.warning('仅支持英文与数字，请切换输入法') }

function applyRememberedAccount(name: string): void {
  const exact = rememberedAccounts.value.find((i) => i.username === name); if (!exact) return
  isApplyingHistory.value = true
  username.value = exact.username; accountQuery.value = exact.username; password.value = exact.password
  rememberAccount.value = true; rememberPassword.value = true; isAutoFilledPassword.value = true; showPassword.value = false
  isApplyingHistory.value = false
}
function removeRememberedAccount(name: string): void {
  auth.removeRememberedPassword(name); rememberedAccounts.value = auth.getRememberedAccounts()
  if (username.value === name) { password.value = ''; rememberPassword.value = false; isAutoFilledPassword.value = false; showPassword.value = false }
}
function handleUsernameSearch(keyword: string): void {
  const f = clean(keyword); if (f !== keyword) warnInvalid(); accountQuery.value = f; username.value = f
  const exact = rememberedAccounts.value.find((i) => i.username === f); if (exact) applyRememberedAccount(exact.username)
}
function handleUsernameSelect(value: string): void { applyRememberedAccount(clean(value)) }
function showAllHistoryAccounts(): void { accountQuery.value = '' }
watch(username, (n, o) => { if (n === o || isApplyingHistory.value) return; password.value = ''; isAutoFilledPassword.value = false; showPassword.value = false })
function handlePasswordInput(v: string): void { const f = clean(v); if (f !== v) { password.value = f; warnInvalid() } isAutoFilledPassword.value = false }
function handlePasswordPaste(e: ClipboardEvent): void { e.preventDefault(); const p = e.clipboardData?.getData('text') || ''; const f = clean(p); if (f !== p) warnInvalid(); password.value += f; isAutoFilledPassword.value = false }

onMounted(() => { document.title = '徽鉴 HuiInsight - 登录'; loadRememberedAccount(); checkBackend() })
async function checkBackend(): Promise<void> { try { const r = await api.system.healthCheck(); backendConnected.value = r.status === 'healthy' || r.status === 'ok' } catch { backendConnected.value = false } }
function loadRememberedAccount(): void {
  rememberedAccounts.value = auth.getRememberedAccounts(); const last = auth.getLastUsername(); if (!last) return
  username.value = last; accountQuery.value = last; rememberAccount.value = true
  const remembered = auth.getRememberedPassword(last)
  if (remembered) { password.value = remembered; rememberPassword.value = true; isAutoFilledPassword.value = true; showPassword.value = false }
}

async function handleLogin(): Promise<void> {
  if (!canLogin.value) return; loginLoading.value = true
  try {
    const finalUsername = username.value.trim(); const loginData = await api.auth.login(finalUsername, password.value)
    auth.saveLoginData(loginData.access_token, loginData.user, rememberAccount.value, finalUsername)
    if (rememberPassword.value) auth.saveRememberedPassword(finalUsername, password.value); else auth.removeRememberedPassword(finalUsername)
    rememberedAccounts.value = auth.getRememberedAccounts()
    permissionStore.bootstrap({ role: loginData.user.role, permissions: loginData.permissions ?? [], role_meta: loginData.role_meta ?? { label: loginData.user.role, color: 'gray', dashboard_view: 'auditor' } })
    Message.success(`欢迎回来，${loginData.user.full_name}`); password.value = ''
    const redirect = route.query.redirect as string; setTimeout(() => router.push(redirect || '/dashboard'), 500)
  } catch (error: any) {
    password.value = ''; const status = error?.response?.status; const detail = error?.response?.data?.detail
    if (status === 401) apiStatus.value = { type: 'error', title: '认证失败', content: detail || '用户名或密码不正确' }
    else if (status === 403) apiStatus.value = { type: 'warning', title: '账户禁用', content: '请联系管理员激活账户' }
    else if (!error?.response) { apiStatus.value = { type: 'error', title: '网络连接失败', content: `无法连接后端 (${apiBaseUrl})，请检查网络或服务状态` }; backendConnected.value = false }
    else if (status >= 500) { apiStatus.value = { type: 'error', title: `服务端异常 (${status})`, content: `${detail || '后端返回 5xx 错误'}，当前目标：${apiBaseUrl}` }; backendConnected.value = true }
    else apiStatus.value = { type: 'error', title: `请求失败 (${status || 'unknown'})`, content: `${detail || '未知错误'}，当前目标：${apiBaseUrl}` }
  } finally { loginLoading.value = false }
}
function showForgetPassword(): void { Message.info('请联系系统管理员重置密码') }
</script>

<style scoped>
.window-chrome{position:fixed;inset:0 0 auto 0;height:40px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:0 14px;z-index:20;background:linear-gradient(180deg,rgba(17,25,42,.92),rgba(14,19,33,.74));border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(12px)}
.chrome-left{display:flex;gap:8px;align-items:center}.dot{width:10px;height:10px;border-radius:50%}.red{background:#f53f3f}.yellow{background:#ff7d00}.green{background:#00b42a}.chrome-title{justify-self:center;color:#c9d1ea;font-size:12px}.chrome-env{justify-self:end;color:#7bc2ff;font-size:11px}
.login-page{min-height:100vh;padding-top:40px;display:flex;justify-content:center;align-items:center;background:radial-gradient(1000px 480px at 90% -10%,rgba(22,93,255,.2),transparent),#0d0f14}
.bg{position:absolute;inset:40px 0 0 0;pointer-events:none}.c{position:absolute;border-radius:50%;filter:blur(86px);opacity:.12}.c1{width:420px;height:420px;background:radial-gradient(circle,#165dff,#00b42a);top:-180px;right:-140px}.c2{width:340px;height:340px;background:radial-gradient(circle,#ff7d00,#f53f3f);bottom:-150px;left:-120px}.c3{width:220px;height:220px;background:radial-gradient(circle,#722ed1,#eb2f96);top:48%;left:6%}
.login-card{width:min(460px,92vw);background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.1);box-shadow:0 10px 42px rgba(0,0,0,.38)}
.card-header{text-align:center;padding:30px 28px 20px;border-bottom:1px solid rgba(255,255,255,.08)}.logo{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:14px}.logo-text{font-weight:700;letter-spacing:1px}.subtitle{display:block;margin-top:8px}
.login-form{padding:30px 28px 26px}.form-item{margin-bottom:20px}.history-account-bar{margin:8px 0 24px;padding:14px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.03)}.history-label{display:block;margin-bottom:9px}.history-tags{display:flex;flex-wrap:wrap;gap:10px}.history-tag{cursor:pointer}.remember-item{margin-top:6px;margin-bottom:26px;display:flex;justify-content:space-between;align-items:center}.remember-options{display:flex;gap:16px}
:deep(.arco-input-wrapper){border-radius:10px;border-color:rgba(255,255,255,.16)!important;background:rgba(255,255,255,.04)!important;transition:all .2s ease}
:deep(.arco-input-wrapper:hover){border-color:rgba(64,128,255,.62)!important;box-shadow:0 4px 14px rgba(29,71,170,.24)}
:deep(.arco-input-wrapper.arco-input-focus){border-color:#4080ff!important;box-shadow:0 0 0 2px rgba(64,128,255,.26),0 8px 24px rgba(30,78,190,.25)!important}
:deep(.arco-auto-complete-dropdown){background:#171f33;border:1px solid rgba(255,255,255,.1)}:deep(.arco-option:hover){background:rgba(64,128,255,.2)}
.login-button{height:46px;border-radius:10px;border:0;background:linear-gradient(135deg,#165dff 0%,#3f8cff 55%,#7aa8ff 100%);transition:transform .2s ease,box-shadow .2s ease}.login-button:hover{transform:translateY(-1px);box-shadow:0 10px 20px rgba(36,98,240,.34)}
.pwd-toggle-btn{padding:0;color:#8ea2d3}.pwd-toggle-btn:hover{color:#c9d7ff}.api-status,.backend-status{margin-top:16px}
</style>
