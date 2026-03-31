/**
 * 数据模型定义
 * @author xuyu
 */

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// 用户角色
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserRole {
    Admin,
    Supervisor,
    Auditor,
    User,
}

impl Default for UserRole {
    fn default() -> Self {
        UserRole::User
    }
}

impl std::fmt::Display for UserRole {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            UserRole::Admin => write!(f, "admin"),
            UserRole::Supervisor => write!(f, "supervisor"),
            UserRole::Auditor => write!(f, "auditor"),
            UserRole::User => write!(f, "user"),
        }
    }
}

impl std::str::FromStr for UserRole {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "admin" => Ok(UserRole::Admin),
            "supervisor" => Ok(UserRole::Supervisor),
            "auditor" => Ok(UserRole::Auditor),
            "user" => Ok(UserRole::User),
            _ => Err(format!("无效的角色: {}", s)),
        }
    }
}

/// 用户状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserStatus {
    pub is_active: bool,
    pub last_login_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Default for UserStatus {
    fn default() -> Self {
        Self {
            is_active: true,
            last_login_at: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }
}

/// 用户信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub display_name: String,
    pub email: Option<String>,
    pub password_hash: String,
    pub role: UserRole,
    pub avatar_url: Option<String>,
    pub status: UserStatus,
}

/// 用户创建请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub display_name: String,
    pub email: Option<String>,
    pub password: String,
    pub role: UserRole,
    pub avatar_url: Option<String>,
}

/// 用户更新请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateUserRequest {
    pub display_name: Option<String>,
    pub email: Option<String>,
    pub avatar_url: Option<String>,
    pub is_active: Option<bool>,
}

/// 用户会话
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserSession {
    pub id: i64,
    pub user_id: i64,
    pub session_token: String,
    pub device_info: Option<String>,
    pub ip_address: Option<String>,
    pub expires_at: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
}

/// 班次类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ShiftType {
    Morning,
    Afternoon,
    Night,
}

impl Default for ShiftType {
    fn default() -> Self {
        ShiftType::Morning
    }
}

impl std::fmt::Display for ShiftType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ShiftType::Morning => write!(f, "morning"),
            ShiftType::Afternoon => write!(f, "afternoon"),
            ShiftType::Night => write!(f, "night"),
        }
    }
}

impl std::str::FromStr for ShiftType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "morning" => Ok(ShiftType::Morning),
            "afternoon" => Ok(ShiftType::Afternoon),
            "night" => Ok(ShiftType::Night),
            _ => Err(format!("无效的班次类型: {}", s)),
        }
    }
}

/// 任务状态
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Completed,
    Cancelled,
}

impl Default for TaskStatus {
    fn default() -> Self {
        TaskStatus::Pending
    }
}

impl std::fmt::Display for TaskStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TaskStatus::Pending => write!(f, "pending"),
            TaskStatus::InProgress => write!(f, "in_progress"),
            TaskStatus::Completed => write!(f, "completed"),
            TaskStatus::Cancelled => write!(f, "cancelled"),
        }
    }
}

impl std::str::FromStr for TaskStatus {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "pending" => Ok(TaskStatus::Pending),
            "in_progress" => Ok(TaskStatus::InProgress),
            "completed" => Ok(TaskStatus::Completed),
            "cancelled" => Ok(TaskStatus::Cancelled),
            _ => Err(format!("无效的任务状态: {}", s)),
        }
    }
}

/// 审核任务
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditTask {
    pub id: i64,
    pub user_id: i64,
    pub task_date: String, // YYYY-MM-DD格式
    pub shift_type: ShiftType,
    pub status: TaskStatus,
    pub total_rooms: i32,
    pub reviewed_rooms: i32,
    pub violation_count: i32,
    pub work_duration: i32, // 分钟
    pub start_time: Option<DateTime<Utc>>,
    pub end_time: Option<DateTime<Utc>>,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 创建审核任务请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateAuditTaskRequest {
    pub task_date: String,
    pub shift_type: ShiftType,
    pub total_rooms: Option<i32>,
    pub notes: Option<String>,
}

/// 更新审核任务请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateAuditTaskRequest {
    pub status: Option<TaskStatus>,
    pub reviewed_rooms: Option<i32>,
    pub violation_count: Option<i32>,
    pub work_duration: Option<i32>,
    pub start_time: Option<DateTime<Utc>>,
    pub end_time: Option<DateTime<Utc>>,
    pub notes: Option<String>,
}

/// 小酒窝语音房间状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct XjwRoomStatus {
    pub is_online: bool,
    pub viewer_count: i32,
    pub last_check_time: Option<DateTime<Utc>>,
}

impl Default for XjwRoomStatus {
    fn default() -> Self {
        Self {
            is_online: false,
            viewer_count: 0,
            last_check_time: None,
        }
    }
}

/// 小酒窝语音房间
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct XjwRoom {
    pub id: i64,
    pub room_id: String,
    pub room_name: String,
    pub anchor_name: String,
    pub category: String,
    pub tags: Vec<String>,
    pub status: XjwRoomStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 违规类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ViolationType {
    Pornographic,      // 色情低俗
    Gambling,          // 赌博
    Fraud,             // 诈骗
    Violence,          // 暴力血腥
    Political,         // 政治敏感
    Copyright,         // 版权侵权
    Other,             // 其他违规
}

impl Default for ViolationType {
    fn default() -> Self {
        ViolationType::Other
    }
}

impl std::fmt::Display for ViolationType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ViolationType::Pornographic => write!(f, "pornographic"),
            ViolationType::Gambling => write!(f, "gambling"),
            ViolationType::Fraud => write!(f, "fraud"),
            ViolationType::Violence => write!(f, "violence"),
            ViolationType::Political => write!(f, "political"),
            ViolationType::Copyright => write!(f, "copyright"),
            ViolationType::Other => write!(f, "other"),
        }
    }
}

impl std::str::FromStr for ViolationType {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "pornographic" => Ok(ViolationType::Pornographic),
            "gambling" => Ok(ViolationType::Gambling),
            "fraud" => Ok(ViolationType::Fraud),
            "violence" => Ok(ViolationType::Violence),
            "political" => Ok(ViolationType::Political),
            "copyright" => Ok(ViolationType::Copyright),
            "other" => Ok(ViolationType::Other),
            _ => Err(format!("无效的违规类型: {}", s)),
        }
    }
}

/// 违规记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ViolationRecord {
    pub id: i64,
    pub task_id: i64,
    pub room_id: i64,
    pub violation_type: ViolationType,
    pub severity: i32, // 1-5级，5为最严重
    pub description: String,
    pub evidence_urls: Vec<String>,
    pub handled_by: Option<i64>, // 处理人ID
    pub handled_at: Option<DateTime<Utc>>,
    pub handling_notes: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 部门信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Department {
    pub id: i64,
    pub name: String,
    pub code: String,
    pub description: Option<String>,
    pub parent_id: Option<i64>,
    pub manager_id: Option<i64>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 员工信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Employee {
    pub id: i64,
    pub user_id: i64,
    pub department_id: i64,
    pub employee_id: String,
    pub position: String,
    pub join_date: String, // YYYY-MM-DD格式
    pub work_status: String, // 在职、离职、休假等
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 绩效统计
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceStats {
    pub id: i64,
    pub user_id: i64,
    pub period: String, // YYYY-MM格式
    pub total_tasks: i32,
    pub completed_tasks: i32,
    pub total_rooms_reviewed: i32,
    pub violation_count: i32,
    pub average_work_duration: f64, // 分钟
    pub quality_score: f64, // 0-100分
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

