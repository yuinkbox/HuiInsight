<template>
  <div class="violation-popup-page">
    <div class="violation-popup-inner">
      <h1 class="violation-popup-title">违规处置上报</h1>
      <a-form :model="form" layout="vertical" class="violation-popup-form">
        <a-form-item label="房间号">
          <a-input v-model="form.room_id" placeholder="自动识别或手动输入">
            <template #prefix><icon-live-broadcast /></template>
          </a-input>
        </a-form-item>
        <a-form-item label="违规主播ID">
          <a-input v-model="form.user_id" placeholder="自动识别或手动输入">
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>
        <a-form-item label="违规原因" required>
          <a-textarea
            v-model="form.reason"
            placeholder="请描述违规行为（如：涉黄、低俗、诱导未成年人等）"
            :max-length="200"
            show-word-limit
            :auto-size="{ minRows: 3, maxRows: 6 }"
          />
        </a-form-item>
        <a-form-item label="处罚动作" required>
          <a-radio-group v-model="form.action" type="button" size="large">
            <a-radio value="ban">
              <icon-stop /> 封禁
            </a-radio>
            <a-radio value="mute">
              <icon-mute /> 禁言
            </a-radio>
            <a-radio value="close_room">
              <icon-poweroff /> 关播
            </a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
      <div class="violation-popup-actions">
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="primary" status="danger" :loading="loading" @click="handleSubmit">
          确认处置
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getBridge, isDesktopMode } from '@/bridge/qt_channel'
import api from '@/api'
import { auth } from '@/utils/auth'

const form = ref({
  room_id: '',
  user_id: '',
  reason: '',
  action: 'ban' as 'ban' | 'mute' | 'close_room',
})

const loading = ref(false)

async function hydrateFromBridge() {
  if (!isDesktopMode()) return
  const bridge = await getBridge()
  if (!bridge) return
  try {
    const raw = await bridge.getRoomInfo()
    const info = JSON.parse(raw)
    form.value.room_id = info.room_id || ''
    form.value.user_id = info.user_id || ''
  } catch {
    /* ignore */
  }
}

onMounted(() => {
  void hydrateFromBridge()
})

function handleCancel() {
  void getBridge().then((b) => b?.closeViolationPopup())
}

async function handleSubmit() {
  if (!form.value.reason.trim()) {
    Message.warning('请填写违规原因')
    return
  }
  loading.value = true
  try {
    const userInfo = auth.getUserInfo()
    await api.post('/api/violation/report', {
      room_id: form.value.room_id,
      user_id: form.value.user_id,
      reason: form.value.reason.trim(),
      action: form.value.action,
      operator: userInfo?.full_name || userInfo?.username || '未知',
      timestamp: new Date().toISOString(),
    })
    const actionLabel = { ban: '封禁', mute: '禁言', close_room: '关播' }[form.value.action]
    const logDetails = `房间${form.value.room_id} 用户${form.value.user_id} ${actionLabel} - ${form.value.reason.trim()}`
    const bridge = await getBridge()
    bridge?.notifyViolationSubmitted(
      JSON.stringify({ type: 'submitted', logDetails }),
    )
    Message.success('违规处置已提交，已通知飞书群')
    bridge?.closeViolationPopup()
  } catch {
    Message.error('违规上报失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.violation-popup-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 20px 24px 28px;
  background: var(--color-bg-1);
}
.violation-popup-inner {
  max-width: 480px;
  margin: 0 auto;
}
.violation-popup-title {
  margin: 0 0 18px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
}
.violation-popup-form :deep(.arco-radio-button) {
  margin-bottom: 6px;
}
.violation-popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
}
</style>
