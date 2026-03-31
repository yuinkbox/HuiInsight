/**
 * 数据库模块
 * 徽鉴HuiInsight - 小酒窝语音审核部门中台系统
 * @author xuyu
 */

pub mod models;
pub mod connection;

// 重新导出常用类型
pub use models::*;
pub use connection::{DatabaseManager, DatabaseError};