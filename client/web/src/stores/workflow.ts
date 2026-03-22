/**
 * Workflow Store — 工作流核心状态全局管理
 *
 * 设计原则：
 * - 路由切换组件销毁时，Store 状态不丢失
 * - 登录/登出时通过 reset() 强制清零
 * - 持久化只在工作流激活时写入 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type WorkStatus = 'offline' | 'patrolling' | 'handling' | 'suspended'

export const useWorkflowStore = defineStore('workflow', () => {
  // ── 核心工作流状态 ──────────────────────────────────────────
  const workStatus          = ref<WorkStatus>('offline')
  const totalSeconds        = ref(0)
  const reviewedCount       = ref(0)
  const violationCount      = ref(0)
  const isHandlingViolation = ref(false)
  const isSuspended         = ref(false)
  const todayTaskId         = ref<number | null>(null)  // 当前任务 ID，用于持久化
  const lastActionTime      = ref<number>(0)

  // ── 计算属性 ────────────────────────────────────────────────
  const isWorking = computed(() => workStatus.value !== 'offline')

  const statusText = computed(() => ({
    offline:    '离线',
    patrolling: '巡查中',
    handling:   '处置中',
    suspended:  '挂起',
  })[workStatus.value])

  // ── 操作 ────────────────────────────────────────────────────
  /** 登录/登出时强制清零，确保新账号白纸状态 */
  function reset(): void {
    workStatus.value          = 'offline'
    totalSeconds.value        = 0
    reviewedCount.value       = 0
    violationCount.value      = 0
    isHandlingViolation.value = false
    isSuspended.value         = false
    todayTaskId.value         = null
    lastActionTime.value      = 0
  }

  /** 序列化到 localStorage（仅在工作流激活时调用） */
  function persist(): void {
    if (!isWorking.value) return
    localStorage.setItem('workflow_state', JSON.stringify({
      workStatus:          workStatus.value,
      totalSeconds:        totalSeconds.value,
      reviewedCount:       reviewedCount.value,
      violationCount:      violationCount.value,
      isHandlingViolation: isHandlingViolation.value,
      isSuspended:         isSuspended.value,
      todayTaskId:         todayTaskId.value,
      lastActionTime:      lastActionTime.value,
      savedAt:             Date.now(),
    }))
  }

  /**
   * 从 localStorage 恢复状态（路由切换回来时调用）
   * 仅在工作流确实处于激活状态时才恢复，避免幽灵数据
   */
  function restore(): boolean {
    const raw = localStorage.getItem('workflow_state')
    if (!raw) return false
    try {
      const s = JSON.parse(raw)
      // 超过 2 小时未活跃，视为过期，自动清除
      if (Date.now() - (s.savedAt ?? 0) > 2 * 60 * 60 * 1000) {
        localStorage.removeItem('workflow_state')
        return false
      }
      if (s.workStatus === 'offline') return false
      workStatus.value          = s.workStatus
      totalSeconds.value        = s.totalSeconds        ?? 0
      reviewedCount.value       = s.reviewedCount       ?? 0
      violationCount.value      = s.violationCount      ?? 0
      isHandlingViolation.value = s.isHandlingViolation ?? false
      isSuspended.value         = s.isSuspended         ?? false
      todayTaskId.value         = s.todayTaskId         ?? null
      lastActionTime.value      = s.lastActionTime      ?? Date.now()
      return true  // 表示成功恢复了活跃工作流
    } catch {
      localStorage.removeItem('workflow_state')
      return false
    }
  }

  /** 工作流结束后清除持久化缓存 */
  function clearPersist(): void {
    localStorage.removeItem('workflow_state')
  }

  return {
    // state
    workStatus,
    totalSeconds,
    reviewedCount,
    violationCount,
    isHandlingViolation,
    isSuspended,
    todayTaskId,
    lastActionTime,
    // computed
    isWorking,
    statusText,
    // methods
    reset,
    persist,
    restore,
    clearPersist,
  }
})
