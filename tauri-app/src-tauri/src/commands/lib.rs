/**
 * Tauri Commands模块
 * @author xuyu
 */

pub mod auth;
pub mod tasks;

// 重新导出认证命令
pub use auth::{
    login, logout, verify_token, check_permission, get_current_user,
    LoginRequest, LoginResponse, UserInfo, PermissionCheckRequest,
    init_auth_manager, AuthManager,
};

// 重新导出任务命令
pub use tasks::{
    get_or_create_today_task, start_audit_task, update_task_progress,
    complete_audit_task, get_user_tasks,
    TodayTaskResponse, WeeklyStats, TaskProgressUpdate,
};