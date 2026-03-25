<template>
  <!-- 强制更新：模态遮罩，不可关闭 -->
  <div v-if="forceUpdate && updateInfo" class="update-mask">
    <div class="update-modal">
      <div class="update-modal__icon">&#x1F504;</div>
      <div class="update-modal__title">发现新版本 {{ updateInfo.version }}</div>
      <div class="update-modal__body">
        当前版本过低，必须更新后才能继续使用。
      </div>
      <div v-if="updateInfo.changelog" class="update-modal__changelog">
        <div class="changelog-label">更新内容：</div>
        <div class="changelog-text">{{ updateInfo.changelog }}</div>
      </div>
      <div class="update-modal__actions">
        <button
          class="btn-update"
          :disabled="downloading || downloaded"
          @click="startDownload"
        >
          <span v-if="!downloading &amp;&amp; !downloaded">立即更新</span>
          <span v-else-if="downloading">下载中 {{ progress }}%</span>
          <span v-else>&#x2705; 下载完成</span>
        </button>
        <button
          v-if="downloaded"
          class="btn-install"
          @click="installNow"
        >
          重启安装
        </button>
      </div>
      <div v-if="downloading" class="progress-bar">
        <div class="progress-bar__fill" :style="{ width: progress + '%' }" />
      </div>
    </div>
  </div>

  <!-- 普通更新：右下角浮动通知条 -->
  <transition name="slide-up">
    <div v-if="!forceUpdate &amp;&amp; updateInfo &amp;&amp; visible" class="update-toast">
      <div class="update-toast__header">
        <span class="update-toast__icon">&#x2B06;</span>
        <span class="update-toast__title">发现新版本 {{ updateInfo.version }}</span>
        <button class="update-toast__close" @click="visible = false">&#x2715;</button>
      </div>
      <div v-if="updateInfo.changelog" class="update-toast__changelog">
        {{ updateInfo.changelog }}
      </div>
      <div class="update-toast__actions">
        <button class="btn-later" @click="visible = false">稍后</button>
        <button
          class="btn-download"
          :disabled="downloading || downloaded"
          @click="startDownload"
        >
          <span v-if="!downloading &amp;&amp; !downloaded">下载更新</span>
          <span v-else-if="downloading">{{ progress }}%</span>
          <span v-else>已下载</span>
        </button>
        <button v-if="downloaded" class="btn-install" @click="installNow">重启安装</button>
      </div>
      <div v-if="downloading" class="progress-bar">
        <div class="progress-bar__fill" :style="{ width: progress + '%' }" />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBridge } from '@/bridge/qt_channel'

interface UpdatePayload {
  version: string
  changelog: string
  download_url: string
  force: boolean
}

const updateInfo   = ref<UpdatePayload | null>(null)
const forceUpdate  = ref(false)
const visible      = ref(true)
const downloading  = ref(false)
const downloaded   = ref(false)
const progress     = ref(0)
const installerPath = ref('')

onMounted(async () => {
  const bridge = await getBridge()
  if (!bridge) return

  // Listen for update available signal
  bridge.updateAvailable?.connect((payload: string) => {
    try {
      const data: UpdatePayload = JSON.parse(payload)
      updateInfo.value  = data
      forceUpdate.value = data.force
      visible.value     = true
    } catch {
      console.warn('[UpdateNotifier] invalid payload', payload)
    }
  })

  // Listen for download progress
  bridge.updateProgress?.connect((pct: number) => {
    progress.value = pct
  })

  // Listen for download ready
  bridge.updateReady?.connect((path: string) => {
    installerPath.value = path
    downloading.value   = false
    downloaded.value    = true
  })
})

function startDownload() {
  if (!updateInfo.value || downloading.value || downloaded.value) return
  downloading.value = true
  progress.value    = 0
  getBridge().then(bridge => {
    bridge?.startDownload(updateInfo.value!.download_url)
  })
}

function installNow() {
  if (!installerPath.value) return
  getBridge().then(bridge => {
    bridge?.startInstallUpdate(installerPath.value)
  })
}
</script>

<style scoped>
/* Force update modal */
.update-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.update-modal {
  background: #1d2129;
  border: 1px solid #2e3443;
  border-radius: 8px;
  padding: 32px;
  width: 380px;
  text-align: center;
  color: #e5e6eb;
}

.update-modal__icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.update-modal__title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #e5e6eb;
}

.update-modal__body {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 16px;
}

.update-modal__changelog {
  background: #272e3b;
  border-radius: 6px;
  padding: 10px 14px;
  text-align: left;
  margin-bottom: 20px;
}

.changelog-label {
  font-size: 11px;
  color: #4e5969;
  margin-bottom: 4px;
}

.changelog-text {
  font-size: 12px;
  color: #c9cdd4;
  line-height: 1.6;
}

.update-modal__actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

/* Toast notification */
.update-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 300px;
  background: #1d2129;
  border: 1px solid #2e3443;
  border-radius: 8px;
  padding: 16px;
  z-index: 9998;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}

.update-toast__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.update-toast__icon {
  font-size: 16px;
}

.update-toast__title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #e5e6eb;
}

.update-toast__close {
  background: none;
  border: none;
  color: #4e5969;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}

.update-toast__close:hover { color: #86909c; }

.update-toast__changelog {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 12px;
  line-height: 1.5;
}

.update-toast__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Buttons */
.btn-later {
  background: #272e3b;
  color: #86909c;
  border: 1px solid #2e3443;
  border-radius: 4px;
  padding: 4px 14px;
  font-size: 12px;
  cursor: pointer;
}

.btn-later:hover { background: #2e3443; color: #c9cdd4; }

.btn-download, .btn-update {
  background: #165dff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 14px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
}

.btn-download:hover, .btn-update:hover { background: #1253e0; }
.btn-download:disabled, .btn-update:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-install {
  background: #00b42a;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 14px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
}

.btn-install:hover { background: #009a24; }

/* Progress bar */
.progress-bar {
  margin-top: 10px;
  height: 4px;
  background: #272e3b;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: #165dff;
  transition: width 0.3s ease;
  border-radius: 2px;
}

/* Toast animation */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
