/**
 * Workflow Store — 工作流核心状态全局管理
 *
 * 设计原则：
 * - 路由切换组件销毁时，Store 状态不丢失
 * - 登录/登出时通过 reset() 强制清零
 * - 持久化只在工作流激活时写入 localStorage
 * - actionLog 存在 Store 中，路由切换不丢失
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type WorkStatus = 'offline' | 'patrolling' | 'handling' | 'suspended'

export interface ActionLogItem {
  id: number
  timestamp: string
  action: string
  details: string
}

export const useWorkflowStore = defineStore('workflow', () => {
  // ── 核心工作流状态 ──────────────────────────────────────────
  const workStatus          = ref<WorkStatus>('offline')
  const totalSeconds        = ref(0)
  const reviewedCount       = ref(0)
  const violationCount      = ref(0)
  const isHandlingViolation = ref(false)
  const isSuspended         = ref(false)
  const todayTaskId         = ref<number | null>(null)
  const lastActionTime      = ref<number>(0)

  // ── 操作日志（存在 Store，路由切换不丢失）─────────────────────────
  const actionLog = ref<ActionLogItem[]>([])

  // ── 计算属性 ──────────────────────────────────────────
  const isWorking = computed(() => workStatus.value !== 'offline')

  const statusText = computed(() => ({
    offline:    '离线',
    patrolling: '巡查中',
    handling:   '处置中',
    suspended:  '挂起',
  })[workStatus.value])

  // ── 操作 ──────────────────────────────────────────

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
    actionLog.value           = []
    localStorage.removeItem('workflow_state')
    localStorage.removeItem('blind_checker_log')
  }

  /** 向 actionLog 添加一条记录，并同步到 localStorage */
  function addActionLog(item: ActionLogItem): void {
    actionLog.value.unshift(item)
    if (actionLog.value.length > 100) actionLog.value = actionLog.value.slice(0, 100)
    localStorage.setItem('blind_checker_log', JSON.stringify(actionLog.value))
  }

  /** 从 localStorage 恢复 actionLog（组件挂载时调用） */
  function restoreActionLog(): void {
    if (actionLog.value.length > 0) return  // Store 已有数据，无需恢复
    const raw = localStorage.getItem('blind_checker_log')
    if (!raw) return
    try {
      const items = JSON.parse(raw)
      if (Array.isArray(items)) actionLog.value = items
    } catch { /* ignore */ }
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
    // actionLog 单独持久化
    localStorage.setItem('blind_checker_log', JSON.stringify(actionLog.value))
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
      // 同步恢复 actionLog
      restoreActionLog()
      return true
    } catch {
      localStorage.removeItem('workflow_state')
      return false
    }
  }

  /** 工作流结束后清除工作流持久化缓存（不清除 actionLog） */
  function clearPersist(): void {
    localStorage.removeItem('workflow_state')
    // 注意：此处故意不清除 blind_checker_log，让日志跳过路由切换仍可查看
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
    actionLog,
    // computed
    isWorking,
    statusText,
    // methods
    reset,
    addActionLog,
    restoreActionLog,
    persist,
    restore,
    clearPersist,
  }
})
