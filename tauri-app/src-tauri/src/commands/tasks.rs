/**
 * 审核任务管理命令
 * @author xuyu
 */

use std::sync::Arc;
use tauri::State;
use chrono::{Utc, Datelike, Duration};
use serde::{Deserialize, Serialize};

use crate::error::{AppError, ErrorResponse};
use crate::database::{DatabaseManager, DatabaseError, AuditTask, TaskStatus, ShiftType, CreateAuditTaskRequest, UpdateAuditTaskRequest};
use crate::AppState;

/// 今日任务响应
#[derive(Debug, Serialize)]
pub struct TodayTaskResponse {
    pub task: Option<AuditTask>,
    pub weekly_stats: WeeklyStats,
}

/// 周统计
#[derive(Debug, Serialize)]
pub struct WeeklyStats {
    pub total_reviewed: i32,
    pub total_violations: i32,
    pub total_duration: i32, // 分钟
    pub task_count: i32,
}

/// 任务进度更新请求
#[derive(Debug, Deserialize)]
pub struct TaskProgressUpdate {
    pub reviewed_rooms: Option<i32>,
    pub violation_count: Option<i32>,
    pub work_duration: Option<i32>, // 分钟
    pub notes: Option<String>,
}

/// 获取或创建今日审核任务命令
#[tauri::command]
pub async fn get_or_create_today_task(
    token: String,
    state: State<'_, AppState>,
) -> Result<TodayTaskResponse, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    let today = Utc::now().format("%Y-%m-%d").to_string();
    
    // 查询今日任务
    let mut stmt = conn.prepare(
        "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
         FROM audit_tasks 
         WHERE user_id = ? AND task_date = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task_result: Result<AuditTask, _> = stmt.query_row([&claims.sub, &today], |row| {
        Ok(AuditTask {
            id: row.get(0)?,
            user_id: row.get(1)?,
            task_date: row.get(2)?,
            shift_type: match row.get::<_, String>(3)?.as_str() {
                "morning" => ShiftType::Morning,
                "afternoon" => ShiftType::Afternoon,
                "night" => ShiftType::Night,
                _ => ShiftType::Morning,
            },
            status: match row.get::<_, String>(4)?.as_str() {
                "pending" => TaskStatus::Pending,
                "in_progress" => TaskStatus::InProgress,
                "completed" => TaskStatus::Completed,
                "cancelled" => TaskStatus::Cancelled,
                _ => TaskStatus::Pending,
            },
            total_rooms: row.get(5)?,
            reviewed_rooms: row.get(6)?,
            violation_count: row.get(7)?,
            work_duration: row.get(8)?,
            start_time: row.get(9)?,
            end_time: row.get(10)?,
            notes: row.get(11)?,
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    });
    
    let task = match task_result {
        Ok(task) => Some(task),
        Err(_) => {
            // 如果没有今日任务，自动创建
            let hour = Utc::now().hour();
            let shift_type = if hour < 12 {
                ShiftType::Morning
            } else if hour < 18 {
                ShiftType::Afternoon
            } else {
                ShiftType::Night
            };
            
            // 插入新任务
            conn.execute(
                "INSERT INTO audit_tasks (user_id, task_date, shift_type, status, total_rooms, 
                                         reviewed_rooms, violation_count, work_duration)
                 VALUES (?, ?, ?, ?, 0, 0, 0, 0)",
                [&claims.sub.to_string(), &today, &shift_type.to_string(), &TaskStatus::Pending.to_string()],
            ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
            
            let task_id = conn.last_insert_rowid();
            
            // 查询新创建的任务
            let mut stmt = conn.prepare(
                "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                        violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
                 FROM audit_tasks 
                 WHERE id = ?"
            ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
            
            let new_task: AuditTask = stmt.query_row([&task_id], |row| {
                Ok(AuditTask {
                    id: row.get(0)?,
                    user_id: row.get(1)?,
                    task_date: row.get(2)?,
                    shift_type: match row.get::<_, String>(3)?.as_str() {
                        "morning" => ShiftType::Morning,
                        "afternoon" => ShiftType::Afternoon,
                        "night" => ShiftType::Night,
                        _ => ShiftType::Morning,
                    },
                    status: match row.get::<_, String>(4)?.as_str() {
                        "pending" => TaskStatus::Pending,
                        "in_progress" => TaskStatus::InProgress,
                        "completed" => TaskStatus::Completed,
                        "cancelled" => TaskStatus::Cancelled,
                        _ => TaskStatus::Pending,
                    },
                    total_rooms: row.get(5)?,
                    reviewed_rooms: row.get(6)?,
                    violation_count: row.get(7)?,
                    work_duration: row.get(8)?,
                    start_time: row.get(9)?,
                    end_time: row.get(10)?,
                    notes: row.get(11)?,
                    created_at: row.get(12)?,
                    updated_at: row.get(13)?,
                })
            }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
            
            Some(new_task)
        }
    };
    
    // 获取本周统计
    let now = Utc::now();
    let week_start = now - Duration::days(now.weekday().num_days_from_monday() as i64);
    let week_start_str = week_start.format("%Y-%m-%d").to_string();
    
    let mut stmt = conn.prepare(
        "SELECT 
            COALESCE(SUM(reviewed_rooms), 0) as total_reviewed,
            COALESCE(SUM(violation_count), 0) as total_violations,
            COALESCE(SUM(work_duration), 0) as total_duration,
            COUNT(*) as task_count
         FROM audit_tasks 
         WHERE user_id = ? AND task_date >= ? AND status = 'completed'"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let weekly_stats: WeeklyStats = stmt.query_row([&claims.sub, &week_start_str], |row| {
        Ok(WeeklyStats {
            total_reviewed: row.get(0)?,
            total_violations: row.get(1)?,
            total_duration: row.get(2)?,
            task_count: row.get(3)?,
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    Ok(TodayTaskResponse {
        task,
        weekly_stats,
    })
}

/// 开始审核任务命令
#[tauri::command]
pub async fn start_audit_task(
    token: String,
    task_id: i64,
    state: State<'_, AppState>,
) -> Result<AuditTask, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 检查任务是否存在且属于当前用户
    let mut stmt = conn.prepare(
        "SELECT user_id FROM audit_tasks WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task_user_id: i64 = stmt.query_row([&task_id], |row| row.get(0))
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    if task_user_id != claims.sub {
        return Err(AppError::PermissionDenied("无权操作此任务".to_string()).into());
    }
    
    // 更新任务状态为进行中，设置开始时间
    conn.execute(
        "UPDATE audit_tasks SET status = 'in_progress', start_time = ? WHERE id = ?",
        [Utc::now().to_rfc3339(), &task_id.to_string()],
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 查询更新后的任务
    let mut stmt = conn.prepare(
        "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
         FROM audit_tasks 
         WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task: AuditTask = stmt.query_row([&task_id], |row| {
        Ok(AuditTask {
            id: row.get(0)?,
            user_id: row.get(1)?,
            task_date: row.get(2)?,
            shift_type: match row.get::<_, String>(3)?.as_str() {
                "morning" => ShiftType::Morning,
                "afternoon" => ShiftType::Afternoon,
                "night" => ShiftType::Night,
                _ => ShiftType::Morning,
            },
            status: match row.get::<_, String>(4)?.as_str() {
                "pending" => TaskStatus::Pending,
                "in_progress" => TaskStatus::InProgress,
                "completed" => TaskStatus::Completed,
                "cancelled" => TaskStatus::Cancelled,
                _ => TaskStatus::Pending,
            },
            total_rooms: row.get(5)?,
            reviewed_rooms: row.get(6)?,
            violation_count: row.get(7)?,
            work_duration: row.get(8)?,
            start_time: row.get(9)?,
            end_time: row.get(10)?,
            notes: row.get(11)?,
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    Ok(task)
}

/// 更新任务进度命令
#[tauri::command]
pub async fn update_task_progress(
    token: String,
    task_id: i64,
    update: TaskProgressUpdate,
    state: State<'_, AppState>,
) -> Result<AuditTask, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 检查任务是否存在且属于当前用户
    let mut stmt = conn.prepare(
        "SELECT user_id FROM audit_tasks WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task_user_id: i64 = stmt.query_row([&task_id], |row| row.get(0))
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    if task_user_id != claims.sub {
        return Err(AppError::PermissionDenied("无权操作此任务".to_string()).into());
    }
    
    // 构建更新SQL
    let mut updates = Vec::new();
    let mut params: Vec<String> = Vec::new();
    
    if let Some(reviewed_rooms) = update.reviewed_rooms {
        updates.push("reviewed_rooms = ?");
        params.push(reviewed_rooms.to_string());
    }
    
    if let Some(violation_count) = update.violation_count {
        updates.push("violation_count = ?");
        params.push(violation_count.to_string());
    }
    
    if let Some(work_duration) = update.work_duration {
        updates.push("work_duration = ?");
        params.push(work_duration.to_string());
    }
    
    if let Some(notes) = update.notes {
        updates.push("notes = ?");
        params.push(notes);
    }
    
    if updates.is_empty() {
        return Err(AppError::ValidationError("没有提供更新数据".to_string()).into());
    }
    
    // 添加任务ID参数
    params.push(task_id.to_string());
    
    // 执行更新
    let sql = format!("UPDATE audit_tasks SET {} WHERE id = ?", updates.join(", "));
    conn.execute(&sql, params.iter().map(|s| s.as_str()).collect::<Vec<&str>>().as_slice())
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 查询更新后的任务
    let mut stmt = conn.prepare(
        "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
         FROM audit_tasks 
         WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task: AuditTask = stmt.query_row([&task_id], |row| {
        Ok(AuditTask {
            id: row.get(0)?,
            user_id: row.get(1)?,
            task_date: row.get(2)?,
            shift_type: match row.get::<_, String>(3)?.as_str() {
                "morning" => ShiftType::Morning,
                "afternoon" => ShiftType::Afternoon,
                "night" => ShiftType::Night,
                _ => ShiftType::Morning,
            },
            status: match row.get::<_, String>(4)?.as_str() {
                "pending" => TaskStatus::Pending,
                "in_progress" => TaskStatus::InProgress,
                "completed" => TaskStatus::Completed,
                "cancelled" => TaskStatus::Cancelled,
                _ => TaskStatus::Pending,
            },
            total_rooms: row.get(5)?,
            reviewed_rooms: row.get(6)?,
            violation_count: row.get(7)?,
            work_duration: row.get(8)?,
            start_time: row.get(9)?,
            end_time: row.get(10)?,
            notes: row.get(11)?,
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    Ok(task)
}

/// 完成任务命令
#[tauri::command]
pub async fn complete_audit_task(
    token: String,
    task_id: i64,
    state: State<'_, AppState>,
) -> Result<AuditTask, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 检查任务是否存在且属于当前用户
    let mut stmt = conn.prepare(
        "SELECT user_id FROM audit_tasks WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task_user_id: i64 = stmt.query_row([&task_id], |row| row.get(0))
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    if task_user_id != claims.sub {
        return Err(AppError::PermissionDenied("无权操作此任务".to_string()).into());
    }
    
    // 更新任务状态为已完成，设置结束时间
    conn.execute(
        "UPDATE audit_tasks SET status = 'completed', end_time = ? WHERE id = ?",
        [Utc::now().to_rfc3339(), &task_id.to_string()],
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    // 查询更新后的任务
    let mut stmt = conn.prepare(
        "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
         FROM audit_tasks 
         WHERE id = ?"
    ).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let task: AuditTask = stmt.query_row([&task_id], |row| {
        Ok(AuditTask {
            id: row.get(0)?,
            user_id: row.get(1)?,
            task_date: row.get(2)?,
            shift_type: match row.get::<_, String>(3)?.as_str() {
                "morning" => ShiftType::Morning,
                "afternoon" => ShiftType::Afternoon,
                "night" => ShiftType::Night,
                _ => ShiftType::Morning,
            },
            status: match row.get::<_, String>(4)?.as_str() {
                "pending" => TaskStatus::Pending,
                "in_progress" => TaskStatus::InProgress,
                "completed" => TaskStatus::Completed,
                "cancelled" => TaskStatus::Cancelled,
                _ => TaskStatus::Pending,
            },
            total_rooms: row.get(5)?,
            reviewed_rooms: row.get(6)?,
            violation_count: row.get(7)?,
            work_duration: row.get(8)?,
            start_time: row.get(9)?,
            end_time: row.get(10)?,
            notes: row.get(11)?,
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    Ok(task)
}

/// 获取用户历史任务命令
#[tauri::command]
pub async fn get_user_tasks(
    token: String,
    start_date: Option<String>,
    end_date: Option<String>,
    state: State<'_, AppState>,
) -> Result<Vec<AuditTask>, ErrorResponse> {
    // 验证令牌
    let claims = state.auth_manager.verify_token(&token)?;
    
    // 获取数据库连接
    let db = state.db_manager.get_connection();
    let conn = db.lock().await;
    
    // 构建查询条件
    let mut conditions = vec!["user_id = ?".to_string()];
    let mut params: Vec<String> = vec![claims.sub.to_string()];
    
    if let Some(start_date) = start_date {
        conditions.push("task_date >= ?".to_string());
        params.push(start_date);
    }
    
    if let Some(end_date) = end_date {
        conditions.push("task_date <= ?".to_string());
        params.push(end_date);
    }
    
    let where_clause = if conditions.is_empty() {
        "".to_string()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };
    
    let sql = format!(
        "SELECT id, user_id, task_date, shift_type, status, total_rooms, reviewed_rooms, 
                violation_count, work_duration, start_time, end_time, notes, created_at, updated_at
         FROM audit_tasks 
         {} 
         ORDER BY task_date DESC, created_at DESC",
        where_clause
    );
    
    let mut stmt = conn.prepare(&sql)
        .map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let tasks_iter = stmt.query_map(params.iter().map(|s| s.as_str()).collect::<Vec<&str>>().as_slice(), |row| {
        Ok(AuditTask {
            id: row.get(0)?,
            user_id: row.get(1)?,
            task_date: row.get(2)?,
            shift_type: match row.get::<_, String>(3)?.as_str() {
                "morning" => ShiftType::Morning,
                "afternoon" => ShiftType::Afternoon,
                "night" => ShiftType::Night,
                _ => ShiftType::Morning,
            },
            status: match row.get::<_, String>(4)?.as_str() {
                "pending" => TaskStatus::Pending,
                "in_progress" => TaskStatus::InProgress,
                "completed" => TaskStatus::Completed,
                "cancelled" => TaskStatus::Cancelled,
                _ => TaskStatus::Pending,
            },
            total_rooms: row.get(5)?,
            reviewed_rooms: row.get(6)?,
            violation_count: row.get(7)?,
            work_duration: row.get(8)?,
            start_time: row.get(9)?,
            end_time: row.get(10)?,
            notes: row.get(11)?,
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    }).map_err(|e| AppError::DatabaseError(e.to_string()))?;
    
    let mut tasks = Vec::new();
    for task_result in tasks_iter {
        tasks.push(task_result.map_err(|e| AppError::DatabaseError(e.to_string()))?);
    }
    
    Ok(tasks)
}