/**
 * API相关类型定义
 * 专为小酒窝语音平台审核部门中台系统设计
 * @author xuyu
 */

/**
 * API响应基础接口
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errorCode?: string
  timestamp: string
}

/**
 * 分页参数
 */
export interface PaginationParams {
  page?: number
  limit?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

/**
 * 登录请求参数
 */
export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

/**
 * 登录响应数据
 */
export interface LoginResponse {
  user: User
  accessToken: string
  refreshToken?: string
  expiresIn: number
  permissions: string[]
}

/**
 * 刷新令牌请求
 */
export interface RefreshTokenRequest {
  refreshToken: string
}

/**
 * 刷新令牌响应
 */
export interface RefreshTokenResponse {
  accessToken: string
  expiresIn: number
}

/**
 * 用户注册请求（仅管理员可用）
 */
export interface RegisterUserRequest {
  employeeId: string
  username: string
  displayName: string
  department: string
  position: string
  role: UserRole
  password: string
  confirmPassword: string
}

/**
 * 用户更新请求
 */
export interface UpdateUserRequest {
  displayName?: string
  department?: string
  position?: string
  avatarUrl?: string
  currentPassword?: string
  newPassword?: string
}

/**
 * 创建审核任务请求
 */
export interface CreateAuditTaskRequest {
  userId: number
  taskDate: string
  shiftId: number
  targetRooms?: number
  notes?: string
}

/**
 * 更新审核任务请求
 */
export interface UpdateAuditTaskRequest {
  status?: TaskStatus
  completedRooms?: number
  violationCount?: number
  workDuration?: number
  startTime?: string
  endTime?: string
  notes?: string
}

/**
 * 开始审核任务请求
 */
export interface StartAuditTaskRequest {
  taskId: number
}

/**
 * 完成审核任务请求
 */
export interface CompleteAuditTaskRequest {
  taskId: number
  notes?: string
}

/**
 * 房间审核请求
 */
export interface RoomAuditRequest {
  taskId: number
  roomId: number
  auditTime: string
  duration: number
  auditResult: AuditResult
  violationType?: string
  violationLevel?: ViolationLevel
  evidenceUrl?: string
  auditorNotes?: string
}

/**
 * 违规上报请求
 */
export interface ReportViolationRequest {
  auditRecordId: number
  violationTypeId: number
  description: string
  evidenceUrl: string
  timestamp: string
}

/**
 * 审核违规请求
 */
export interface ReviewViolationRequest {
  reviewStatus: ReviewStatus
  reviewNotes?: string
}

/**
 * 添加小酒窝语音房间请求
 */
export interface AddXjwRoomRequest {
  roomId: string
  roomName: string
  hostId: string
  hostName: string
  category?: string
  tags?: string[]
  followerCount?: number
  riskLevel?: 'low' | 'medium' | 'high'
  isMonitored?: boolean
}

/**
 * 更新房间信息请求
 */
export interface UpdateXjwRoomRequest {
  roomName?: string
  category?: string
  tags?: string[]
  followerCount?: number
  isLive?: boolean
  lastLiveTime?: string
  riskLevel?: 'low' | 'medium' | 'high'
  isMonitored?: boolean
}

/**
 * 统计查询参数
 */
export interface StatisticsQueryParams {
  startDate: string
  endDate: string
  userId?: number
  department?: string
  shiftId?: number
}

/**
 * 用户统计响应
 */
export interface UserStatisticsResponse {
  userId: number
  employeeId: string
  displayName: string
  department: string
  position: string
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
  dailyStats: AuditStatistics[]
}

/**
 * 部门统计响应
 */
export interface DepartmentStatisticsResponse {
  department: string
  totalAuditors: number
  activeAuditors: number
  totalTasks: number
  totalRooms: number
  totalViolations: number
  avgEfficiency: number
  avgQuality: number
  dailyStats: DepartmentStatistics[]
  auditorRankings: AuditorPerformance[]
}

/**
 * 实时监控数据
 */
export interface RealtimeMonitorData {
  activeTasks: number
  activeAuditors: number
  roomsBeingAudited: number
  violationsToday: number
  recentViolations: ViolationRecord[]
}

/**
 * 审核员绩效查询参数
 */
export interface AuditorPerformanceQueryParams {
  startDate: string
  endDate: string
  department?: string
  limit?: number
}

/**
 * 审核员绩效响应
 */
export interface AuditorPerformanceResponse {
  rankings: AuditorPerformance[]
  totalAuditors: number
  avgEfficiency: number
  avgQuality: number
}

/**
 * 违规统计查询参数
 */
export interface ViolationStatisticsQueryParams {
  startDate: string
  endDate: string
  department?: string
  level?: ViolationLevel
}

/**
 * 违规统计响应
 */
export interface ViolationStatisticsResponse {
  totalViolations: number
  byType: ViolationStatistics[]
  byDepartment: Array<{
    department: string
    violationCount: number
  }>
  byDate: Array<{
    date: string
    violationCount: number
  }>
}

/**
 * 系统信息响应
 */
export interface SystemInfoResponse {
  appVersion: string
  platformName: string
  rustVersion: string
  nodeVersion: string
  platform: string
  arch: string
  databaseSize: number
  uptime: number
  memoryUsage: number
  totalUsers: number
  totalRooms: number
  totalTasks: number
}

/**
 * 备份请求参数
 */
export interface BackupRequest {
  backupName?: string
  includeData: boolean
  includeLogs: boolean
  includeConfig: boolean
}

/**
 * 备份响应
 */
export interface BackupResponse {
  backupId: string
  backupPath: string
  backupSize: number
  createdAt: string
}

/**
 * 恢复请求参数
 */
export interface RestoreRequest {
  backupId: string
  restoreData: boolean
  restoreLogs: boolean
  restoreConfig: boolean
}

/**
 * 文件上传响应
 */
export interface FileUploadResponse {
  fileId: string
  fileName: string
  fileSize: number
  fileUrl: string
  uploadedAt: string
}

/**
 * 错误响应
 */
export interface ErrorResponse {
  success: false
  errorCode: string
  message: string
  details?: any
  timestamp: string
}

/**
 * 验证错误详情
 */
export interface ValidationErrorDetail {
  field: string
  message: string
  code: string
}

/**
 * 验证错误响应
 */
export interface ValidationErrorResponse extends ErrorResponse {
  details: ValidationErrorDetail[]
}

/**
 * Tauri命令响应包装器
 */
export interface TauriCommandResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

/**
 * 数据库查询参数
 */
export interface DatabaseQueryParams {
  table: string
  where?: Record<string, any>
  orderBy?: string
  orderDirection?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

/**
 * 数据库更新参数
 */
export interface DatabaseUpdateParams {
  table: string
  data: Record<string, any>
  where: Record<string, any>
}

/**
 * 数据库插入参数
 */
export interface DatabaseInsertParams {
  table: string
  data: Record<string, any>
}

/**
 * 数据库删除参数
 */
export interface DatabaseDeleteParams {
  table: string
  where: Record<string, any>
}

/**
 * 今日任务查询响应
 */
export interface TodayTasksResponse {
  tasks: TodayAuditTask[]
  totalTasks: number
  completedTasks: number
  inProgressTasks: number
}

/**
 * 实时审核状态响应
 */
export interface RealtimeAuditStatusResponse {
  activeTasks: RealtimeAuditStatus[]
  totalActive: number
  totalCompletedToday: number
}

/**
 * 房间搜索参数
 */
export interface RoomSearchParams {
  keyword?: string
  category?: string
  riskLevel?: 'low' | 'medium' | 'high'
  isLive?: boolean
  isMonitored?: boolean
  page?: number
  limit?: number
}

/**
 * 房间搜索响应
 */
export interface RoomSearchResponse {
  rooms: XjwRoom[]
  total: number
  page: number
  limit: number
}

/**
 * 批量操作请求
 */
export interface BatchOperationRequest {
  operation: 'update' | 'delete'
  table: string
  ids: number[]
  data?: Record<string, any>
}

/**
 * 批量操作响应
 */
export interface BatchOperationResponse {
  success: boolean
  processed: number
  succeeded: number
  failed: number
  errors?: string[]
}

/**
 * 数据导出请求
 */
export interface ExportDataRequest {
  dataType: 'tasks' | 'violations' | 'statistics' | 'logs'
  startDate?: string
  endDate?: string
  format: 'csv' | 'json' | 'excel'
  includeHeaders?: boolean
}

/**
 * 数据导出响应
 */
export interface ExportDataResponse {
  exportId: string
  fileName: string
  fileSize: number
  downloadUrl: string
  expiresAt: string
}