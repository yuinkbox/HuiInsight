/**
 * 徽鉴HuiInsight - 小酒窝语音审核部门中台系统
 * Tauri应用主库
 * @author xuyu
 */

// 导出模块
pub mod error;
pub mod config;
pub mod database;
pub mod commands;

// 重新导出常用类型
pub use error::{AppError, ErrorResponse};
pub use config::{AppConfig, ConfigManager};
pub use database::{DatabaseManager, DatabaseError};
pub use commands::{AuthManager, init_auth_manager};

/// 应用状态
pub struct AppState {
    pub config: AppConfig,
    pub db_manager: std::sync::Arc<DatabaseManager>,
    pub auth_manager: std::sync::Arc<AuthManager>,
}

impl AppState {
    /// 创建新的应用状态
    pub async fn new() -> Result<Self, AppError> {
        // 加载配置
        let config_manager = ConfigManager::new();
        let config = config_manager.load_config().await?;
        
        // 创建数据库管理器
        let db_path = config.database.path.clone();
        let db_manager = DatabaseManager::new(&db_path)
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        
        // 执行数据库迁移
        db_manager.run_migrations().await
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        
        // 创建认证管理器
        let db_manager_arc = std::sync::Arc::new(db_manager);
        let auth_manager = init_auth_manager(db_manager_arc.clone());
        
        Ok(Self {
            config,
            db_manager: db_manager_arc,
            auth_manager,
        })
    }
    
    /// 检查应用状态
    pub async fn check(&self) -> Result<(), AppError> {
        // 检查数据库连接
        self.db_manager.check_connection().await
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        
        Ok(())
    }
}

/// 初始化应用
pub async fn init_app() -> Result<AppState, AppError> {
    let app_state = AppState::new().await?;
    
    // 检查应用状态
    app_state.check().await?;
    
    println!("应用初始化完成");
    Ok(app_state)
}