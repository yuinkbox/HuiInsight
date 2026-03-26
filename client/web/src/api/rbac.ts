/**
 * RBAC ????? API ??
 *
 * ????:
 * - UserRole ???????? server/constants/roles.py ??
 * - ?????????? usePermissionStore().can() ??????????
 * - ?????????? + API ????
 */

import api from './index'

// ---------------------------------------------------------------------------
// ???? ? ?????? UserRole ???
// ---------------------------------------------------------------------------
export enum UserRole {
  MANAGER       = 'manager',
  TEAM_LEADER   = 'team_leader',
  QA_SPECIALIST = 'qa_specialist',
  ADMIN_SUPPORT = 'admin_support',
  AUDITOR       = 'auditor',
}

// ---------------------------------------------------------------------------
// ????
// ---------------------------------------------------------------------------
export enum ShiftType {
  MORNING   = 'morning',
  AFTERNOON = 'afternoon',
  NIGHT     = 'night',
}

export enum TaskChannel {
  IMAGE = 'image',
  CHAT  = 'chat',
  VIDEO = 'video',
  LIVE  = 'live',
}

// ---------------------------------------------------------------------------
// ????
// ---------------------------------------------------------------------------
export interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at?: string
}

export interface TaskAssignment {
  user_id: number
  username: string
  full_name: string
  task_channel: string
  historical_count: number
}

export interface DispatchRequest {
  shift_date: string
  shift_type: ShiftType
  user_ids: number[]
  required_channels: TaskChannel[]
}

export interface DispatchResponse {
  shift_date: string
  shift_type: string
  assignments: TaskAssignment[]
  summary: {
    total_assignments: number
    channel_distribution: Record<string, number>
    algorithm: string
    timestamp: string
  }
}

export interface TaskItem {
  id: number
  shift_date: string
  shift_type: string
  task_channel: string
  user_id: number
  is_completed: boolean
  reviewed_count: number
  violation_count: number
  work_duration: number
  user_info?: {
    username: string
    full_name: string
    role: string
  }
}

export interface UserTaskResponse {
  today_tasks: TaskItem[]
  historical_tasks: TaskItem[]
  weekly_stats: {
    total_reviewed: number
    total_violations: number
    total_duration: number
    task_count: number
    week: number
    year: number
  }
}

export interface TeamInsightRequest {
  start_date: string
  end_date: string
  user_ids?: number[]
  channels?: TaskChannel[]
}

export interface TeamInsightResponse {
  period: { start: string; end: string }
  user_stats: Array<{
    user_id: number
    username: string
    full_name: string
    total_tasks: number
    total_reviewed: number
    total_violations: number
    total_duration: number
    violation_rate: number
    channels: Record<string, { count: number; reviewed: number; violations: number }>
  }>
  channel_stats: Array<{
    channel: string
    total_tasks: number
    total_reviewed: number
    total_violations: number
    avg_reviewed_per_task: number
    unique_users: number
  }>
  overall_stats: {
    period_start: string
    period_end: string
    total_tasks: number
    total_users: number
    total_reviewed: number
    total_violations: number
    total_duration: number
    avg_reviewed_per_user: number
    channels_covered: number
  }
}

export interface ActiveUser {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_superuser: boolean
}

export interface ActionLogItem {
  id: number
  user_id: number
  username: string
  action: string
  details: string
  task_id?: number
  duration?: number
  timestamp: string
}

export interface UsernameChangeRequestItem {
  id: number
  applicant_user_id: number
  old_username: string
  new_username: string
  reason?: string
  status: 'pending' | 'approved' | 'rejected' | 'superseded' | 'cancelled'
  reviewer_user_id?: number
  review_comment?: string
  reviewed_at?: string
  created_at: string
  updated_at?: string
}

// ---------------------------------------------------------------------------
// API ????
// ---------------------------------------------------------------------------
export const rbacApi = {
  /** 获取或自动创建今日直播巡查任务（审核员默认任务，无需派发） */
  async getOrCreateLivePatrolTask(): Promise<TaskItem> {
    return api.get('/api/task/my/live-patrol') as any
  },

  /** 获取我的任务列表 */
  async getMyTasks(): Promise<UserTaskResponse> {
    return api.get('/api/task/my') as any
  },

  /** ?????? */
  async dispatchTasks(request: DispatchRequest): Promise<DispatchResponse> {
    return api.post('/api/dispatch/auto', request) as any
  },

  /** ???????? */
  async getTeamInsight(request: TeamInsightRequest): Promise<TeamInsightResponse> {
    const params: Record<string, string> = {
      start_date: request.start_date,
      end_date: request.end_date,
    }
    if (request.user_ids?.length) params.user_ids = request.user_ids.join(',')
    if (request.channels?.length) params.channels = request.channels.join(',')
    return api.get('/api/team/insight', { params }) as any
  },

  /** ???????? */
  async getActiveUsers(role?: string): Promise<{ users: ActiveUser[]; count: number; filter_role: string }> {
    const params = role ? { role } : {}
    return api.get('/api/users/active', { params }) as any
  },

  /** ??????????????????? */
  async logAction(action: string, details: string, duration?: number, taskId?: number): Promise<void> {
    try {
      await api.post('/api/log/action', {
        action,
        details,
        duration,
        task_id: taskId,
        timestamp: new Date().toISOString(),
      })
    } catch {
      // ?????????????
    }
  },

  /** 获取全部用户（含停用） */
  async getAllUsers(role?: string, isActive?: boolean): Promise<{ users: ActiveUser[]; count: number; filter_role: string }> {
    const params: Record<string, string> = {}
    if (role) params.role = role
    if (isActive !== undefined) params.is_active = String(isActive)
    return api.get('/api/users/all', { params }) as any
  },

  /** 发起我的用户名变更申请 */
  async createMyUsernameChangeRequest(newUsername: string, reason?: string): Promise<UsernameChangeRequestItem> {
    return api.post('/api/users/me/username-change-requests', {
      new_username: newUsername,
      reason: reason || undefined,
    }) as any
  },

  /** 获取我的用户名变更申请记录 */
  async getMyUsernameChangeRequests(): Promise<{ items: UsernameChangeRequestItem[]; total: number }> {
    return api.get('/api/users/me/username-change-requests') as any
  },

  /** 管理端：查询用户名变更申请 */
  async getUsernameChangeRequests(statusFilter?: string): Promise<{ items: UsernameChangeRequestItem[]; total: number }> {
    const params = statusFilter ? { status_filter: statusFilter } : {}
    return api.get('/api/users/username-change-requests', { params }) as any
  },

  /** 管理端：审批通过用户名变更 */
  async approveUsernameChangeRequest(requestId: number, comment?: string): Promise<{ success: boolean; message: string }> {
    return api.post(`/api/users/username-change-requests/${requestId}/approve`, { comment: comment || undefined }) as any
  },

  /** 管理端：驳回用户名变更 */
  async rejectUsernameChangeRequest(requestId: number, comment?: string): Promise<{ success: boolean; message: string }> {
    return api.post(`/api/users/username-change-requests/${requestId}/reject`, { comment: comment || undefined }) as any
  },

  /** 新增用户 */
  async createUser(data: {
    username: string
    full_name: string
    password: string
    email?: string | undefined
    role: string
    is_active: boolean
  }): Promise<ActiveUser> {
    return api.post('/api/users/', data) as any
  },

  /** 获取单个用户详情 */
  async getUser(userId: number): Promise<ActiveUser> {
    return api.get(`/api/users/${userId}`) as any
  },

  /** 更新用户资料（姓名/邮箱/角色/状态） */
  async updateUser(userId: number, data: {
    full_name?: string
    email?: string
    role?: string
    is_active?: boolean
  }): Promise<ActiveUser> {
    return api.put(`/api/users/${userId}`, data) as any
  },

  /** 仅更新用户角色 */
  async updateUserRole(userId: number, newRole: string): Promise<{ success: boolean; message: string }> {
    return api.put(`/api/users/${userId}/role`, { role: newRole }) as any
  },

  /** 切换用户启用/停用状态 */
  async toggleUserStatus(userId: number): Promise<{ success: boolean; message: string }> {
    return api.put(`/api/users/${userId}/status`) as any
  },

  /** 重置用户密码 */
  async resetUserPassword(userId: number, newPassword: string): Promise<{ success: boolean; message: string }> {
    return api.post(`/api/users/${userId}/reset-password`, { new_password: newPassword }) as any
  },

  /** 删除用户 */
  async deleteUser(userId: number): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/users/${userId}`) as any
  },

  /** ???????? */
  async getUserDetailedStats(userId: number, startDate?: string, endDate?: string): Promise<any> {
    const params: Record<string, string> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get(`/api/team/user/${userId}/stats`, { params }) as any
  },

  /** 更新任务进度 */
  async updateTaskProgress(
    taskId: number,
    data: { reviewed_count?: number; violation_count?: number; work_duration?: number; is_completed?: boolean },
  ): Promise<void> {
    try {
      await api.patch(`/api/task/${taskId}/progress`, data)
    } catch (err) {
      console.error('[rbacApi] updateTaskProgress failed, taskId=' + taskId, err)
    }
  },

  /** 完成任务 */
  async completeTask(taskId: number): Promise<void> {
    try {
      await api.post(`/api/task/${taskId}/complete`)
    } catch (err) {
      console.error('[rbacApi] completeTask failed, taskId=' + taskId, err)
    }
  },

  /** 获取当前用户自己的操作日志（无需特殊权限，用于历史记录持久化） */
  async getMyActionLogs(params?: {
    action?: string
    start_time?: string
    end_time?: string
    page?: number
    page_size?: number
  }): Promise<{ items: ActionLogItem[]; total: number; page: number; page_size: number }> {
    return api.get('/api/log/my', { params }) as any
  },

  /** ?????????????? */
  async getActionLogs(params?: {
    user_id?: number
    action?: string
    start_time?: string
    end_time?: string
    page?: number
    page_size?: number
  }): Promise<{ items: ActionLogItem[]; total: number; page: number; page_size: number }> {
    return api.get('/api/log/list', { params }) as any
  },
}

// ---------------------------------------------------------------------------
// ???? ? ???????????
// ---------------------------------------------------------------------------
export function getTaskChannelLabel(channel: string): string {
  const labels: Record<string, string> = {
    image: '图片审核',
    chat:  '单聊审核',
    video: '视频审核',
    live:  '直播巡查',
  }
  return labels[channel] ?? channel
}

export function getShiftTypeLabel(shiftType: string): string {
  const labels: Record<string, string> = {
    morning:   '早班',
    afternoon: '中班',
    night:     '晚班',
  }
  return labels[shiftType] ?? shiftType
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [
    h.toString().padStart(2, '0'),
    m.toString().padStart(2, '0'),
    s.toString().padStart(2, '0'),
  ].join(':')
}
