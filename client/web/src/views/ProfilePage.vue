<template>
  <div class="profile-page">
    <div class="hero-card">
      <div class="hero-head">
        <div>
          <h2>账号身份资料</h2>
          <p>按字节风格打造的审批流：提交后由风控经理审批生效</p>
        </div>
        <a-tag color="blue">
          Username Governance
        </a-tag>
      </div>

      <div class="identity-row">
        <span class="label">当前登录名</span>
        <span class="value">@{{ currentUsername }}</span>
      </div>

      <a-form
        layout="vertical"
        :model="form"
        class="request-form"
      >
        <a-form-item label="申请新用户名">
          <a-input
            v-model="form.newUsername"
            placeholder="2-32位，仅英文/数字/下划线"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="申请说明（可选）">
          <a-textarea
            v-model="form.reason"
            :max-length="255"
            placeholder="例如：统一工号命名"
          />
        </a-form-item>
        <div class="ops">
          <a-button
            type="primary"
            :loading="submitting"
            @click="submitRequest"
          >
            提交审批申请
          </a-button>
          <a-button @click="loadMine">
            刷新记录
          </a-button>
        </div>
      </a-form>
    </div>

    <div class="list-card">
      <div class="list-title">
        我的用户名变更记录
      </div>
      <a-table
        :data="myRequests"
        row-key="id"
        :pagination="{ pageSize: 6 }"
      >
        <template #columns>
          <a-table-column
            title="申请时间"
            :width="180"
          >
            <template #cell="{ record }">
              {{ formatTime(record.created_at) }}
            </template>
          </a-table-column>
          <a-table-column
            title="变更"
            :width="240"
          >
            <template #cell="{ record }">
              {{ record.old_username }} → {{ record.new_username }}
            </template>
          </a-table-column>
          <a-table-column
            title="状态"
            :width="120"
          >
            <template #cell="{ record }">
              <a-tag :color="statusColor(record.status)">
                {{ statusText(record.status) }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="审批备注">
            <template #cell="{ record }">
              {{ record.review_comment || '—' }}
            </template>
          </a-table-column>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { rbacApi, type UsernameChangeRequestItem } from '@/api/rbac'
import { auth } from '@/utils/auth'

const form = ref({ newUsername: '', reason: '' })
const submitting = ref(false)
const myRequests = ref<UsernameChangeRequestItem[]>([])

const currentUsername = computed(() => (auth.getUserInfo() as any)?.username || '')

function normalize(v: string): string {
  return String(v || '').trim().toLowerCase()
}

function isValidUsername(v: string): boolean {
  return /^[a-zA-Z0-9_]{2,32}$/.test(v)
}

function statusText(status: string): string {
  return ({ pending: '待审批', approved: '已通过', rejected: '已驳回', superseded: '已覆盖', cancelled: '已取消' } as any)[status] || status
}

function statusColor(status: string): string {
  return ({ pending: 'arcoblue', approved: 'green', rejected: 'red', superseded: 'orange', cancelled: 'gray' } as any)[status] || 'gray'
}

function formatTime(v: string): string {
  return v ? new Date(v).toLocaleString('zh-CN') : '—'
}

async function loadMine(): Promise<void> {
  try {
    const res = await rbacApi.getMyUsernameChangeRequests()
    myRequests.value = res.items || []
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '加载申请记录失败')
  }
}

async function submitRequest(): Promise<void> {
  const next = normalize(form.value.newUsername)
  if (!isValidUsername(next)) {
    Message.warning('用户名需为 2-32 位英文、数字或下划线')
    return
  }
  if (next === normalize(currentUsername.value)) {
    Message.warning('新用户名不能与当前用户名相同')
    return
  }

  submitting.value = true
  try {
    await rbacApi.createMyUsernameChangeRequest(next, form.value.reason.trim())
    Message.success('申请已提交，等待风控经理审批')
    form.value.newUsername = ''
    form.value.reason = ''
    await loadMine()
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '提交申请失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadMine)
</script>

<style scoped>
.profile-page { display: grid; grid-template-columns: 1fr; gap: 16px; }
.hero-card,.list-card{background:linear-gradient(160deg,rgba(25,31,45,.95),rgba(17,21,31,.95));border:1px solid rgba(84,122,255,.2);border-radius:14px;padding:18px;box-shadow:0 12px 28px rgba(7,14,33,.35)}
.hero-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}
.hero-head h2{margin:0;font-size:20px;color:#ecf2ff;font-weight:700}
.hero-head p{margin:6px 0 0;color:#9fb1d8;font-size:12px}
.identity-row{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.identity-row .label{color:#7d8fb8;font-size:12px}
.identity-row .value{color:#62a6ff;font-size:16px;font-weight:700}
.request-form{max-width:560px}
.ops{display:flex;gap:10px}
.list-title{color:#e7eeff;font-size:14px;font-weight:600;margin-bottom:10px}
</style>
