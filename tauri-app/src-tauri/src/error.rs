/**
 * 错误类型定义
 * @author xuyu
 */

use thiserror::Error;

/// 应用错误类型
#[derive(Error, Debug)]
pub enum AppError {
    /// 数据库错误
    #[error("数据库错误: {0}")]
    DatabaseError(#[from] rusqlite::Error),
    
    /// IO错误
    #[error("IO错误: {0}")]
    IoError(#[from] std::io::Error),
    
    /// JSON序列化错误
    #[error("JSON序列化错误: {0}")]
    JsonError(#[from] serde_json::Error),
    
    /// JWT错误
    #[error("JWT错误: {0}")]
    JwtError(#[from] jsonwebtoken::errors::Error),
    
    /// 加密错误
    #[error("加密错误: {0}")]
    CryptoError(#[from] bcrypt::BcryptError),
    
    /// UUID错误
    #[error("UUID错误: {0}")]
    UuidError(#[from] uuid::Error),
    
    /// 验证错误
    #[error("验证错误: {0}")]
    ValidationError(String),
    
    /// 认证错误
    #[error("认证错误: {0}")]
    AuthError(String),
    
    /// 权限错误
    #[error("权限错误: {0}")]
    PermissionError(String),
    
    /// 业务逻辑错误
    #[error("业务错误: {0}")]
    BusinessError(String),
    
    /// 配置错误
    #[error("配置错误: {0}")]
    ConfigError(String),
    
    /// 未知错误
    #[error("未知错误: {0}")]
    UnknownError(String),
}

/// 结果类型别名
pub type Result<T> = std::result::Result<T, AppError>;

/// 错误代码定义
pub mod error_codes {
    // 认证相关错误
    pub const AUTH_INVALID_CREDENTIALS: &str = "AUTH_001";
    pub const AUTH_TOKEN_EXPIRED: &str = "AUTH_002";
    pub const AUTH_TOKEN_INVALID: &str = "AUTH_003";
    pub const AUTH_USER_NOT_FOUND: &str = "AUTH_004";
    pub const AUTH_USER_INACTIVE: &str = "AUTH_005";
    
    // 权限相关错误
    pub const PERMISSION_DENIED: &str = "PERM_001";
    pub const ROLE_NOT_ALLOWED: &str = "PERM_002";
    
    // 数据相关错误
    pub const DATA_NOT_FOUND: &str = "DATA_001";
    pub const DATA_VALIDATION_FAILED: &str = "DATA_002";
    pub const DATA_CONFLICT: &str = "DATA_003";
    pub const DATA_INTEGRITY_ERROR: &str = "DATA_004";
    
    // 业务逻辑错误
    pub const BUSINESS_INVALID_STATE: &str = "BIZ_001";
    pub const BUSINESS_OPERATION_FAILED: &str = "BIZ_002";
    pub const BUSINESS_LIMIT_EXCEEDED: &str = "BIZ_003";
    
    // 系统错误
    pub const SYSTEM_ERROR: &str = "SYS_001";
    pub const CONFIG_ERROR: &str = "SYS_002";
    pub const NETWORK_ERROR: &str = "SYS_003";
    pub const FILE_SYSTEM_ERROR: &str = "SYS_004";
}

/// 错误响应结构
#[derive(Debug, serde::Serialize)]
pub struct ErrorResponse {
    pub success: bool,
    pub error_code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
    pub timestamp: String,
}

impl ErrorResponse {
    /// 创建错误响应
    pub fn new(error_code: &str, message: &str) -> Self {
        Self {
            success: false,
            error_code: error_code.to_string(),
            message: message.to_string(),
            details: None,
            timestamp: chrono::Local::now().to_rfc3339(),
        }
    }
    
    /// 添加错误详情
    pub fn with_details(mut self, details: serde_json::Value) -> Self {
        self.details = Some(details);
        self
    }
}

/// 从AppError转换为ErrorResponse
impl From<AppError> for ErrorResponse {
    fn from(error: AppError) -> Self {
        match error {
            AppError::AuthError(msg) => ErrorResponse::new(error_codes::AUTH_INVALID_CREDENTIALS, &msg),
            AppError::PermissionError(msg) => ErrorResponse::new(error_codes::PERMISSION_DENIED, &msg),
            AppError::ValidationError(msg) => ErrorResponse::new(error_codes::DATA_VALIDATION_FAILED, &msg),
            AppError::BusinessError(msg) => ErrorResponse::new(error_codes::BUSINESS_OPERATION_FAILED, &msg),
            AppError::DatabaseError(e) => ErrorResponse::new(error_codes::DATA_INTEGRITY_ERROR, &format!("数据库操作失败: {}", e)),
            AppError::ConfigError(msg) => ErrorResponse::new(error_codes::CONFIG_ERROR, &msg),
            _ => ErrorResponse::new(error_codes::SYSTEM_ERROR, &format!("系统错误: {}", error)),
        }
    }
}

/// Tauri命令错误处理
pub fn handle_tauri_error(error: AppError) -> String {
    let error_response: ErrorResponse = error.into();
    serde_json::to_string(&error_response).unwrap_or_else(|_| "{\"success\":false,\"error_code\":\"SYS_001\",\"message\":\"序列化错误\"}".to_string())
}