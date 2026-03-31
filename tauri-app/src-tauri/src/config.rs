/**
 * 配置管理模块
 * @author xuyu
 */

use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use crate::error::{AppError, Result};

/// 应用配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// 数据库配置
    pub database: DatabaseConfig,
    
    /// 认证配置
    pub auth: AuthConfig,
    
    /// 应用配置
    pub app: ApplicationConfig,
    
    /// 日志配置
    pub log: LogConfig,
    
    /// 系统配置
    pub system: SystemConfig,
}

/// 数据库配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    /// 数据库文件路径
    pub path: String,
    
    /// 连接池大小
    pub pool_size: u32,
    
    /// 连接超时时间（秒）
    pub connection_timeout: u64,
    
    /// 是否启用WAL模式
    pub enable_wal: bool,
    
    /// 是否启用外键约束
    pub enable_foreign_keys: bool,
    
    /// 自动备份配置
    pub backup: BackupConfig,
}

/// 备份配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupConfig {
    /// 是否启用自动备份
    pub enabled: bool,
    
    /// 备份间隔（小时）
    pub interval_hours: u32,
    
    /// 保留备份数量
    pub keep_count: u32,
    
    /// 备份目录
    pub backup_dir: String,
}

/// 认证配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    /// JWT密钥
    pub jwt_secret: String,
    
    /// JWT过期时间（小时）
    pub jwt_expiry_hours: u32,
    
    /// 刷新令牌过期时间（天）
    pub refresh_token_expiry_days: u32,
    
    /// 密码加密强度
    pub bcrypt_cost: u32,
    
    /// 最大登录失败次数
    pub max_login_attempts: u32,
    
    /// 账户锁定时间（分钟）
    pub lockout_duration_minutes: u32,
}

/// 应用配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplicationConfig {
    /// 应用名称
    pub name: String,
    
    /// 应用版本
    pub version: String,
    
    /// 作者
    pub author: String,
    
    /// 默认语言
    pub default_language: String,
    
    /// 默认主题
    pub default_theme: String,
    
    /// 自动检查更新
    pub auto_check_updates: bool,
    
    /// 更新检查间隔（天）
    pub update_check_interval_days: u32,
}

/// 日志配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogConfig {
    /// 日志级别
    pub level: String,
    
    /// 日志文件路径
    pub file_path: String,
    
    /// 最大日志文件大小（MB）
    pub max_file_size_mb: u32,
    
    /// 保留日志文件数量
    pub max_file_count: u32,
    
    /// 是否启用控制台输出
    pub enable_console: bool,
    
    /// 是否启用文件输出
    pub enable_file: bool,
}

/// 系统配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemConfig {
    /// 系统托盘配置
    pub system_tray: SystemTrayConfig,
    
    /// 全局快捷键配置
    pub global_shortcuts: GlobalShortcutConfig,
    
    /// 窗口配置
    pub window: WindowConfig,
    
    /// 通知配置
    pub notification: NotificationConfig,
}

/// 系统托盘配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemTrayConfig {
    /// 是否启用系统托盘
    pub enabled: bool,
    
    /// 托盘图标路径
    pub icon_path: String,
    
    /// 左键点击行为
    pub left_click_action: String,
    
    /// 右键菜单配置
    pub context_menu: ContextMenuConfig,
}

/// 上下文菜单配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextMenuConfig {
    /// 是否显示"显示窗口"菜单项
    pub show_show_window: bool,
    
    /// 是否显示"隐藏窗口"菜单项
    pub show_hide_window: bool,
    
    /// 是否显示"退出"菜单项
    pub show_quit: bool,
    
    /// 自定义菜单项
    pub custom_items: Vec<CustomMenuItem>,
}

/// 自定义菜单项
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CustomMenuItem {
    /// 菜单项ID
    pub id: String,
    
    /// 菜单项文本
    pub text: String,
    
    /// 是否启用
    pub enabled: bool,
    
    /// 快捷键
    pub shortcut: Option<String>,
}

/// 全局快捷键配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalShortcutConfig {
    /// 是否启用全局快捷键
    pub enabled: bool,
    
    /// 显示/隐藏窗口快捷键
    pub toggle_window: String,
    
    /// 截图快捷键
    pub screenshot: String,
    
    /// 快速报告快捷键
    pub quick_report: String,
}

/// 窗口配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowConfig {
    /// 窗口宽度
    pub width: u32,
    
    /// 窗口高度
    pub height: u32,
    
    /// 最小宽度
    pub min_width: u32,
    
    /// 最小高度
    pub min_height: u32,
    
    /// 是否可调整大小
    pub resizable: bool,
    
    /// 是否全屏
    pub fullscreen: bool,
    
    /// 是否始终置顶
    pub always_on_top: bool,
    
    /// 是否显示装饰
    pub decorations: bool,
    
    /// 是否透明
    pub transparent: bool,
    
    /// 是否跳过任务栏
    pub skip_taskbar: bool,
    
    /// 窗口主题
    pub theme: String,
}

/// 通知配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationConfig {
    /// 是否启用通知
    pub enabled: bool,
    
    /// 通知声音
    pub sound: bool,
    
    /// 通知持续时间（秒）
    pub duration_seconds: u32,
    
    /// 通知位置
    pub position: String,
    
    /// 通知类型配置
    pub types: NotificationTypes,
}

/// 通知类型配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationTypes {
    /// 违规警报通知
    pub violation_alert: bool,
    
    /// 任务完成通知
    pub task_completed: bool,
    
    /// 系统通知
    pub system_notification: bool,
    
    /// 更新通知
    pub update_notification: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            database: DatabaseConfig::default(),
            auth: AuthConfig::default(),
            app: ApplicationConfig::default(),
            log: LogConfig::default(),
            system: SystemConfig::default(),
        }
    }
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            path: "huiinsight.db".to_string(),
            pool_size: 5,
            connection_timeout: 30,
            enable_wal: true,
            enable_foreign_keys: true,
            backup: BackupConfig::default(),
        }
    }
}

impl Default for BackupConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            interval_hours: 24,
            keep_count: 7,
            backup_dir: "backups".to_string(),
        }
    }
}

impl Default for AuthConfig {
    fn default() -> Self {
        Self {
            jwt_secret: "default-jwt-secret-key-change-in-production".to_string(),
            jwt_expiry_hours: 24,
            refresh_token_expiry_days: 7,
            bcrypt_cost: 12,
            max_login_attempts: 5,
            lockout_duration_minutes: 30,
        }
    }
}

impl Default for ApplicationConfig {
    fn default() -> Self {
        Self {
            name: "徽鉴HuiInsight".to_string(),
            version: "1.0.0".to_string(),
            author: "xuyu".to_string(),
            default_language: "zh-CN".to_string(),
            default_theme: "light".to_string(),
            auto_check_updates: true,
            update_check_interval_days: 7,
        }
    }
}

impl Default for LogConfig {
    fn default() -> Self {
        Self {
            level: "info".to_string(),
            file_path: "logs/app.log".to_string(),
            max_file_size_mb: 10,
            max_file_count: 5,
            enable_console: true,
            enable_file: true,
        }
    }
}

impl Default for SystemConfig {
    fn default() -> Self {
        Self {
            system_tray: SystemTrayConfig::default(),
            global_shortcuts: GlobalShortcutConfig::default(),
            window: WindowConfig::default(),
            notification: NotificationConfig::default(),
        }
    }
}

impl Default for SystemTrayConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            icon_path: "icons/tray-icon.png".to_string(),
            left_click_action: "toggle".to_string(),
            context_menu: ContextMenuConfig::default(),
        }
    }
}

impl Default for ContextMenuConfig {
    fn default() -> Self {
        Self {
            show_show_window: true,
            show_hide_window: true,
            show_quit: true,
            custom_items: vec![],
        }
    }
}

impl Default for GlobalShortcutConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            toggle_window: "Ctrl+Shift+H".to_string(),
            screenshot: "Ctrl+Shift+S".to_string(),
            quick_report: "Ctrl+Shift+R".to_string(),
        }
    }
}

impl Default for WindowConfig {
    fn default() -> Self {
        Self {
            width: 1200,
            height: 800,
            min_width: 800,
            min_height: 600,
            resizable: true,
            fullscreen: false,
            always_on_top: false,
            decorations: true,
            transparent: false,
            skip_taskbar: false,
            theme: "system".to_string(),
        }
    }
}

impl Default for NotificationConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            sound: true,
            duration_seconds: 5,
            position: "top-right".to_string(),
            types: NotificationTypes::default(),
        }
    }
}

impl Default for NotificationTypes {
    fn default() -> Self {
        Self {
            violation_alert: true,
            task_completed: true,
            system_notification: true,
            update_notification: true,
        }
    }
}

/// 配置管理器
pub struct ConfigManager {
    config: AppConfig,
    config_path: PathBuf,
}

impl ConfigManager {
    /// 创建配置管理器
    pub fn new(config_path: Option<PathBuf>) -> Result<Self> {
        let config_path = config_path.unwrap_or_else(|| {
            let mut path = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
            path.push("徽鉴HuiInsight");
            path.push("config.json");
            path
        });
        
        let config = if config_path.exists() {
            Self::load_config(&config_path)?
        } else {
            let config = AppConfig::default();
            Self::save_config(&config_path, &config)?;
            config
        };
        
        Ok(Self {
            config,
            config_path,
        })
    }
    
    /// 加载配置
    fn load_config(path: &PathBuf) -> Result<AppConfig> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| AppError::ConfigError(format!("读取配置文件失败: {}", e)))?;
        
        serde_json::from_str(&content)
            .map_err(|e| AppError::ConfigError(format!("解析配置文件失败: {}", e)))
    }
    
    /// 保存配置
    fn save_config(path: &PathBuf, config: &AppConfig) -> Result<()> {
        // 确保目录存在
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| AppError::ConfigError(format!("创建配置目录失败: {}", e)))?;
        }
        
        let content = serde_json::to_string_pretty(config)
            .map_err(|e| AppError::ConfigError(format!("序列化配置失败: {}", e)))?;
        
        std::fs::write(path, content)
            .map_err(|e| AppError::ConfigError(format!("写入配置文件失败: {}", e)))
    }
    
    /// 获取配置
    pub fn get_config(&self) -> &AppConfig {
        &self.config
    }
    
    /// 更新配置
    pub fn update_config(&mut self, config: AppConfig) -> Result<()> {
        self.config = config;
        self.save()
    }
    
    /// 保存配置
    pub fn save(&self) -> Result<()> {
        Self::save_config(&self.config_path, &self.config)
    }
    
    /// 获取配置路径
    pub fn config_path(&self) -> &PathBuf {
        &self.config_path
    }
    
    /// 重新加载配置
    pub fn reload(&mut self) -> Result<()> {
        self.config = Self::load_config(&self.config_path)?;
        Ok(())
    }
    
    /// 重置为默认配置
    pub fn reset_to_default(&mut self) -> Result<()> {
        self.config = AppConfig::default();
        self.save()
    }
}