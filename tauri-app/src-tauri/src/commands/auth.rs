/**
 * 用户认证和权限管理命令
 * @author xuyu
 */

use std::sync::Arc;
use tauri::State;
use chrono::{Utc, Duration};
use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use argon2::{self, Config, ThreadMode, Variant, Version};
use rand::Rng;

use crate::error::{AppError, ErrorResponse};
use crate::database::{DatabaseManager, DatabaseError, User, UserRole, UserSession};
use crate::AppState;

/// JWT令牌配置
#[derive(Debug, Clone)]
pub struct JwtConfig {
    pub secret: String,
    pub expiration_hours: i64,
}

impl Default for JwtConfig {
    fn default() -> Self {
        Self {
            secret: "your-secret-key-change-in-production".to_string(),
            expiration_hours: 24,
        }
    }
}

/// JWT声明
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: i64, // 用户ID
    pub username: String,
    pub role: String,
    pub exp: usize, // 过期时间
    pub iat: usize, // 签发时间
}

/// 登录请求
#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
    pub remember_me: Option<bool>,
}

/// 登录响应
#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub user: UserInfo,
    pub permissions: Vec<String>,
}

/// 用户信息
#[derive(Debug, Serialize)]
pub struct UserInfo {
    pub id: i64,
    pub username: String,
    pub display_name: String,
    pub email: Option<String>,
    pub role: UserRole,
    pub avatar_url: Option<String>,
    pub department: Option<DepartmentInfo>,
}

/// 部门信息
#[derive(Debug, Serialize)]
pub struct DepartmentInfo {
    pub id: i64,
    pub name: String,
    pub code: String,
}

/// 权限检查请求
#[derive(Debug, Deserialize)]
pub struct PermissionCheckRequest {
    pub permission: String,
}

/// 认证管理器
pub struct AuthManager {
    jwt_config: JwtConfig,
    db_manager: Arc<DatabaseManager>,
}

impl AuthManager {
    /// 创建新的认证管理器
    pub fn new(jwt_config: JwtConfig, db_manager: Arc<DatabaseManager>) -> Self {
        Self {
            jwt_config,
            db_manager,
        }
    }
    
    /// 验证用户密码
    fn verify_password(&self, password: &str, hash: &str) -> Result<bool, AppError> {
        argon2::verify_encoded(hash, password.as_bytes())
            .map_err(|e| AppError::AuthenticationError(format!("密码验证失败: {}", e)))
    }
    
    /// 生成密码哈希
    fn hash_password(&self, password: &str) -> Result<String, AppError> {
        let salt: [u8; 32] = rand::thread_rng().gen();
        let config = Config {
            variant: Variant::Argon2id,
            version: Version::Version13,
            mem_cost: 4096,
            time_cost: 3,
            lanes: 4,
            thread_mode: ThreadMode::Parallel,
            secret: &[],
            ad: &[],
            hash_length: 32,
        };
        
        argon2::hash_encoded(password.as_bytes(), &salt, &config)
            .map_err(|e| AppError::AuthenticationError(format!("密码哈希生成失败: {}", e)))
    }
    
    /// 生成JWT令牌
    fn generate_token(&self, user: &User) -> Result<String, AppError> {
        let now = Utc::now();
        let exp = now + Duration::hours(self.jwt_config.expiration_hours);
        
        let claims = Claims {
            sub: user.id,
            username: user.username.clone(),
            role: user.role.to_string(),
            exp: exp.timestamp() as usize,
            iat: now.timestamp() as usize,
        };
        
        encode(&Header::default(), &claims, &EncodingKey::from_secret(self.jwt_config.secret.as_ref()))
            .map_err(|e| AppError::AuthenticationError(format!("JWT生成失败: {}", e)))
    }
    
    /// 验证JWT令牌
    pub fn verify_token(&self, token: &str) -> Result<Claims, AppError> {
        let token_data = decode::<Claims>(
            token,
            &DecodingKey::from_secret(self.jwt_config.secret.as_ref()),
            &Validation::default(),
        ).map_err(|e| AppError::AuthenticationError(format!("JWT验证失败: {}", e)))?;
        
        Ok(token_data.claims)
    }
    
    /// 获取用户权限
    fn get_user_permissions(&self, role: &UserRole) -> Vec<String> {
        match role {
            UserRole::Admin => vec![
                "user:manage".to_string(),
                "department:manage".to_string(),
                "task:manage".to_string(),
                "violation:manage".to_string(),
                "statistics:view".to_string(),
                "system:config".to_string(),
            ],
            UserRole::Supervisor => vec![
                "user:view".to_string(),
                "task:assign".to_string(),
                "violation:review".to_string(),
                "statistics:view".to_string(),
                "performance:view".to_string(),
            ],
            UserRole::Auditor => vec![
                "task:view".to_string(),
                "task:execute".to_string(),
                "violation:report".to_string(),
                "statistics:self".to_string(),
            ],
            UserRole::User => vec![
                "task:view".to_string(),
                "statistics:self".to_string(),
            ],
        }
    }
}

/// 用户登录命令
#[tauri::command]
pub async fn login(
    request: LoginRequest,
    state: State<'_, AppState>,
) -> Result<LoginResponse, ErrorResponse> {
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 查询用户
    let mut stmt = conn.prepare(
        "SELECT id, username, display_name, email, password_hash, role, avatar_url, is_active 
         FROM users WHERE username = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let user_result: Result<User, _> = stmt.query_row([&request.username], |row| {
        Ok(User {
            id: row.get(0)?,
            username: row.get(1)?,
            display_name: row.get(2)?,
            email: row.get(3)?,
            password_hash: row.get(4)?,
            role: match row.get::<_, String>(5)?.as_str() {
                "admin" => UserRole::Admin,
                "supervisor" => UserRole::Supervisor,
                "auditor" => UserRole::Auditor,
                _ => UserRole::User,
            },
            avatar_url: row.get(6)?,
            status: crate::database::UserStatus {
                is_active: row.get(7)?,
                last_login_at: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            },
        })
    });
    
    let user = match user_result {
        Ok(user) => user,
        Err(_) => return Err(AppError::AuthenticationError("用户名或密码错误".to_string()).into()),
    };
    
    // 检查用户是否激活
    if !user.status.is_active {
        return Err(AppError::AuthenticationError("用户账户已被禁用".to_string()).into());
    }
    
    // 验证密码
    if !state.auth_manager.verify_password(&request.password, &user.password_hash)? {
        return Err(AppError::AuthenticationError("用户名或密码错误".to_string()).into());
    }
    
    // 生成JWT令牌
    let token = state.auth_manager.generate_token(&user)?;
    
    // 更新最后登录时间
    conn.execute(
        "UPDATE users SET last_login_at = ? WHERE id = ?",
        [Utc::now().to_rfc3339(), &user.id.to_string()],
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 创建用户会话
    let session_token = uuid::Uuid::new_v4().to_string();
    let expires_at = Utc::now() + Duration::hours(if request.remember_me.unwrap_or(false) { 720 } else { 24 });
    
    conn.execute(
        "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
        [&user.id.to_string(), &session_token, &expires_at.to_rfc3339()],
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 获取部门信息
    let department_info: Option<DepartmentInfo> = {
        let mut stmt = conn.prepare(
            "SELECT d.id, d.name, d.code FROM departments d
             JOIN employees e ON d.id = e.department_id
             WHERE e.user_id = ?"
        ).ok();
        
        if let Some(ref mut stmt) = stmt {
            stmt.query_row([&user.id], |row| {
                Ok(DepartmentInfo {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    code: row.get(2)?,
                })
            }).ok()
        } else {
            None
        }
    };
    
    // 获取用户权限
    let permissions = state.auth_manager.get_user_permissions(&user.role);
    
    // 构建响应
    Ok(LoginResponse {
        token,
        user: UserInfo {
            id: user.id,
            username: user.username,
            display_name: user.display_name,
            email: user.email,
            role: user.role,
            avatar_url: user.avatar_url,
            department: department_info,
        },
        permissions,
    })
}

/// 用户注销命令
#[tauri::command]
pub async fn logout(
    token: String,
    state: State<'_, AppState>,
) -> Result<(), ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 删除用户会话
    conn.execute(
        "DELETE FROM user_sessions WHERE user_id = ? AND session_token = ?",
        [&claims.sub.to_string(), &token],
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    Ok(())
}

/// 验证令牌命令
#[tauri::command]
pub async fn verify_token(
    token: String,
    state: State<'_, AppState>,
) -> Result<UserInfo, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 查询用户信息
    let mut stmt = conn.prepare(
        "SELECT id, username, display_name, email, role, avatar_url, is_active 
         FROM users WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let user: User = stmt.query_row([&claims.sub], |row| {
        Ok(User {
            id: row.get(0)?,
            username: row.get(1)?,
            display_name: row.get(2)?,
            email: row.get(3)?,
            password_hash: "".to_string(), // 不返回密码哈希
            role: match row.get::<_, String>(4)?.as_str() {
                "admin" => UserRole::Admin,
                "supervisor" => UserRole::Supervisor,
                "auditor" => UserRole::Auditor,
                _ => UserRole::User,
            },
            avatar_url: row.get(5)?,
            status: crate::database::UserStatus {
                is_active: row.get(6)?,
                last_login_at: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            },
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 检查用户是否激活
    if !user.status.is_active {
        return Err(AppError::AuthenticationError("用户账户已被禁用".to_string()).into());
    }
    
    // 获取部门信息
    let department_info: Option<DepartmentInfo> = {
        let mut stmt = conn.prepare(
            "SELECT d.id, d.name, d.code FROM departments d
             JOIN employees e ON d.id = e.department_id
             WHERE e.user_id = ?"
        ).ok();
        
        if let Some(ref mut stmt) = stmt {
            stmt.query_row([&user.id], |row| {
                Ok(DepartmentInfo {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    code: row.get(2)?,
                })
            }).ok()
        } else {
            None
        }
    };
    
    Ok(UserInfo {
        id: user.id,
        username: user.username,
        display_name: user.display_name,
        email: user.email,
        role: user.role,
        avatar_url: user.avatar_url,
        department: department_info,
    })
}

/// 检查权限命令
#[tauri::command]
pub async fn check_permission(
    token: String,
    request: PermissionCheckRequest,
    state: State<'_, AppState>,
) -> Result<bool, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 查询用户角色
    let mut stmt = conn.prepare(
        "SELECT role FROM users WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let role_str: String = stmt.query_row([&claims.sub], |row| row.get(0))
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let role = match role_str.as_str() {
        "admin" => UserRole::Admin,
        "supervisor" => UserRole::Supervisor,
        "auditor" => UserRole::Auditor,
        _ => UserRole::User,
    };
    
    // 获取用户权限
    let permissions = state.auth_manager.get_user_permissions(&role);
    
    // 检查权限
    Ok(permissions.contains(&request.permission))
}

/// 获取当前用户信息命令
#[tauri::command]
pub async fn get_current_user(
    token: String,
    state: State<'_, AppState>,
) -> Result<UserInfo, ErrorResponse> {
    verify_token(token, state).await
}

/// 初始化认证管理器
pub fn init_auth_manager(db_manager: Arc<DatabaseManager>) -> Arc<AuthManager> {
    let jwt_config = JwtConfig::default();
    Arc::new(AuthManager::new(jwt_config, db_manager))
}