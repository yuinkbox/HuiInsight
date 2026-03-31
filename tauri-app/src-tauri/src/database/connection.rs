/**
 * 数据库连接管理
 * @author xuyu
 */

use std::path::Path;
use std::sync::Arc;
use tokio::sync::Mutex;
use rusqlite::{Connection, OpenFlags, params};
use anyhow::{Result, Context};

/// 数据库连接管理器
pub struct DatabaseManager {
    connection: Arc<Mutex<Connection>>,
}

impl DatabaseManager {
    /// 创建新的数据库管理器
    pub fn new(db_path: &str) -> Result<Self> {
        let path = Path::new(db_path);
        
        // 确保数据库目录存在
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                std::fs::create_dir_all(parent)
                    .context("创建数据库目录失败")?;
            }
        }
        
        // 打开数据库连接
        let connection = Connection::open_with_flags(
            path,
            OpenFlags::SQLITE_OPEN_READ_WRITE
                | OpenFlags::SQLITE_OPEN_CREATE
                | OpenFlags::SQLITE_OPEN_FULL_MUTEX,
        ).context("打开数据库连接失败")?;
        
        // 启用外键约束
        connection.execute("PRAGMA foreign_keys = ON;", [])
            .context("启用外键约束失败")?;
        
        // 启用WAL模式以提高并发性能
        connection.execute("PRAGMA journal_mode = WAL;", [])
            .context("启用WAL模式失败")?;
        
        // 设置同步模式为NORMAL（性能与安全性的平衡）
        connection.execute("PRAGMA synchronous = NORMAL;", [])
            .context("设置同步模式失败")?;
        
        // 设置缓存大小
        connection.execute("PRAGMA cache_size = -10000;", [])
            .context("设置缓存大小失败")?;
        
        Ok(Self {
            connection: Arc::new(Mutex::new(connection)),
        })
    }
    
    /// 获取数据库连接
    pub fn get_connection(&self) -> Arc<Mutex<Connection>> {
        self.connection.clone()
    }
    
    /// 执行数据库迁移
    pub async fn run_migrations(&self) -> Result<()> {
        let conn = self.connection.lock().await;
        
        // 创建迁移表（如果不存在）
        conn.execute(
            "CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        ).context("创建迁移表失败")?;
        
        // 获取已应用的迁移
        let mut stmt = conn.prepare(
            "SELECT name FROM migrations ORDER BY id"
        ).context("准备查询迁移语句失败")?;
        
        let applied_migrations: Vec<String> = stmt
            .query_map([], |row| row.get(0))
            .context("查询迁移记录失败")?
            .collect::<Result<Vec<String>, _>>()
            .context("解析迁移记录失败")?;
        
        // 执行所有迁移
        for migration in MIGRATIONS.iter() {
            if !applied_migrations.contains(&migration.name.to_string()) {
                println!("执行迁移: {}", migration.name);
                
                // 开始事务
                let tx = conn.transaction().context("开始事务失败")?;
                
                // 执行迁移SQL
                tx.execute_batch(migration.sql)
                    .context(format!("执行迁移SQL失败: {}", migration.name))?;
                
                // 记录迁移
                tx.execute(
                    "INSERT INTO migrations (name) VALUES (?)",
                    params![migration.name],
                ).context("记录迁移失败")?;
                
                // 提交事务
                tx.commit().context("提交事务失败")?;
                
                println!("迁移完成: {}", migration.name);
            }
        }
        
        Ok(())
    }
    
    /// 检查数据库连接
    pub async fn check_connection(&self) -> Result<()> {
        let conn = self.connection.lock().await;
        conn.execute("SELECT 1", [])
            .context("数据库连接检查失败")?;
        Ok(())
    }
    
    /// 备份数据库
    pub async fn backup(&self, backup_path: &str) -> Result<()> {
        let conn = self.connection.lock().await;
        
        // 创建备份连接
        let backup_conn = Connection::open(backup_path)
            .context("打开备份数据库失败")?;
        
        // 执行备份
        conn.backup(rusqlite::DatabaseName::Main, &backup_conn, rusqlite::DatabaseName::Main)
            .context("数据库备份失败")?;
        
        Ok(())
    }
    
    /// 执行数据库维护
    pub async fn maintenance(&self) -> Result<()> {
        let conn = self.connection.lock().await;
        
        // 执行VACUUM以优化数据库文件大小
        conn.execute("VACUUM", [])
            .context("执行VACUUM失败")?;
        
        // 重新分析统计信息
        conn.execute("ANALYZE", [])
            .context("执行ANALYZE失败")?;
        
        Ok(())
    }
}

/// 迁移定义
struct Migration {
    name: &'static str,
    sql: &'static str,
}

/// 数据库迁移列表
const MIGRATIONS: &[Migration] = &[
    Migration {
        name: "001_initial_schema",
        sql: include_str!("../../migrations/001_initial_schema.sql"),
    },
    Migration {
        name: "002_add_performance_stats",
        sql: include_str!("../../migrations/002_add_performance_stats.sql"),
    },
];

/// 数据库错误类型
#[derive(Debug, thiserror::Error)]
pub enum DatabaseError {
    #[error("数据库连接失败: {0}")]
    ConnectionError(String),
    
    #[error("SQL执行失败: {0}")]
    SqlError(String),
    
    #[error("数据不存在")]
    NotFound,
    
    #[error("数据已存在")]
    AlreadyExists,
    
    #[error("数据验证失败: {0}")]
    ValidationError(String),
    
    #[error("事务失败: {0}")]
    TransactionError(String),
    
    #[error("未知错误: {0}")]
    Unknown(String),
}

impl From<rusqlite::Error> for DatabaseError {
    fn from(err: rusqlite::Error) -> Self {
        match err {
            rusqlite::Error::QueryReturnedNoRows => DatabaseError::NotFound,
            rusqlite::Error::SqliteFailure(err, _) => {
                if err.code == rusqlite::ErrorCode::ConstraintViolation {
                    DatabaseError::AlreadyExists
                } else {
                    DatabaseError::SqlError(err.to_string())
                }
            }
            _ => DatabaseError::SqlError(err.to_string()),
        }
    }
}