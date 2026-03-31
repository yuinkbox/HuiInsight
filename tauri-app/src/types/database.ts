/**
 * 数据库相关类型定义
 * 专为小酒窝语音平台审核部门中台系统设计
 * @author xuyu
 */

/**
 * 用户角色类型
 */
export type UserRole = 'admin' | 'supervisor' | 'auditor'

/**
 * 用户状态
 */
export interface UserStatus {
  isActive: boolean
  lastLoginAt?: string
  createdAt: string
  updatedAt: string
}

/**
 * 用户信息
 */
export interface User {
  id: number
  employeeId: string
  username: string
  displayName: string
  department: string
  position: string
  role: UserRole
  avatarUrl?: string
  status: UserStatus
}

/**
 * 用户会话
 */
export interface UserSession {
  id: number
  userId: number
  sessionToken: string
  deviceInfo?: string
  ipAddress?: string
  expiresAt: string
  createdAt: string
}

/**
 * 审核班次
 */
export interface AuditShift {
  id: number
  shiftName: string
  startTime: string
  endTime: string
  description?: string
  isActive: boolean
  createdAt: string
}

/**
 * 任务状态
 */
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled'

/**
 * 审核任务
 */
export interface AuditTask {
  id: number
  userId: number
  taskDate: string
  shiftId: number
  status: TaskStatus
  targetRooms: number
  completedRooms: number
  violationCount: number
  workDuration: number
  startTime?: string
  endTime?: string
  notes?: string
  createdAt: string
  updatedAt: string
}

/**
 * 小酒窝语音房间
 */
export interface XjwRoom {
  id: number
  roomId: string
  roomName: string
  hostId: string
  hostName: string
  category?: string
  tags?: string[]
  followerCount: number
  isLive: boolean
  lastLiveTime?: string
  riskLevel: 'low' | 'medium' | 'high'
  isMonitored: boolean
  createdAt: string
  updatedAt: string
}

/**
 * 房间审核结果
 */
export type AuditResult = 'normal' | 'warning' | 'violation'

/**
 * 违规等级
 */
export type ViolationLevel = 'minor' | 'major' | 'critical'

/**
 * 房间审核记录
 */
export interface RoomAuditRecord {
  id: number
  taskId: number
  roomId: number
  auditTime: string
  duration: number
  auditResult: AuditResult
  violationType?: string
  violationLevel?: ViolationLevel
  evidenceUrl?: string
  auditorNotes?: string
  supervisorReview?: string
  createdAt: string
}

/**
 * 违规类型
 */
export interface ViolationType {
  id: number
  violationCode: string
  violationName: string
  description: string
  level: ViolationLevel
  penaltyPoints: number
  penaltyAction?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

/**
 * 审核状态
 */
export type ReviewStatus = 'pending' | 'confirmed' | 'rejected'

/**
 * 违规记录
 */
export interface ViolationRecord {
  id: number
  auditRecordId: number
  violationTypeId: number
  description: string
  evidenceUrl: string
  timestamp: string
  reviewerId?: number
  reviewStatus: ReviewStatus
  reviewNotes?: string
  reviewedAt?: string
  createdAt: string
}

/**
 * 审核统计
 */
export interface AuditStatistics {
  id: number
  userId: number
  statDate: string
  totalTasks: number
  completedTasks: number
  totalRooms: number
  completedRooms: number
  totalViolations: number
  minorViolations: number
  majorViolations: number
  criticalViolations: number
  totalDuration: number
  efficiencyScore: number
  qualityScore: number
  createdAt: string
  updatedAt: string
}

/**
 * 部门统计
 */
export interface DepartmentStatistics {
  id: number
  department: string
  statDate: string
  totalAuditors: number
  activeAuditors: number
  totalTasks: number
  totalRooms: number
  totalViolations: number
  avgEfficiency: number
  avgQuality: number
  createdAt: string
}

/**
 * 系统配置
 */
export interface SystemConfig {
  id: number
  configKey: string
  configValue: string
  description?: string
  category: string
  isEncrypted: boolean
  createdAt: string
  updatedAt: string
}

/**
 * 操作日志
 */
export interface OperationLog {
  id: number
  userId?: number
  operationType: string
  operationTarget?: string
  operationDetail?: string
  ipAddress?: string
  userAgent?: string
  success: boolean
  errorMessage?: string
  createdAt: string
}

/**
 * 同步队列状态
 */
export type SyncStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * 同步队列项
 */
export interface SyncQueueItem {
  id: number
  operation: string
  tableName: string
  recordId?: number
  data: string
  status: SyncStatus
  retryCount: number
  lastError?: string
  nextRetryAt?: string
  createdAt: string
  updatedAt: string
}

/**
 * 文件同步状态
 */
export type FileSyncStatus = 'pending' | 'uploading' | 'completed' | 'failed'

/**
 * 文件同步队列项
 */
export interface FileSyncQueueItem {
  id: number
  filePath: string
  fileType: string
  syncStatus: FileSyncStatus
  uploadProgress: number
  cloudUrl?: string
  localHash?: string
  remoteHash?: string
  retryCount: number
  createdAt: string
  updatedAt: string
}

/**
 * 审核员绩效数据
 */
export interface AuditorPerformance {
  userId: number
  employeeId: string
  displayName: string
  department: string
  position: string
  totalTasks: number
  completedTasks: number
  totalRooms: number
  totalViolations: number
  avgEfficiency: number
  avgQuality: number
}

/**
 * 实时审核状态
 */
export interface RealtimeAuditStatus {
  taskId: number
  employeeId: string
  displayName: string
  department: string
  shiftName: string
  status: TaskStatus
  completedRooms: number
  targetRooms: number
  violationCount: number
  workDuration: number
  elapsedMinutes: number
}

/**
 * 违规统计数据
 */
export interface ViolationStatistics {
  violationCode: string
  violationName: string
  level: ViolationLevel
  violationCount: number
  violationDate: string
  department: string
}

/**
 * 今日审核任务
 */
export interface TodayAuditTask {
  taskId: number
  employeeId: string
  displayName: string
  department: string
  taskDate: string
  shiftName: string
  status: TaskStatus
  completedRooms: number
  targetRooms: number
  violationCount: number
  workDuration: number
  startTime?: string
  endTime?: string
}