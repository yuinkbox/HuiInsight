-- 初始数据库架构
-- 徽鉴HuiInsight - 小酒窝语音审核部门中台系统
-- @author xuyu

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- admin, supervisor, auditor, user
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT NOT NULL UNIQUE,
    device_info TEXT,
    ip_address TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 部门表
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER,
    manager_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- 员工表
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    employee_id TEXT NOT NULL UNIQUE,
    position TEXT NOT NULL,
    join_date TEXT NOT NULL, -- YYYY-MM-DD格式
    work_status TEXT NOT NULL DEFAULT '在职', -- 在职、离职、休假等
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 小酒窝语音房间表
CREATE TABLE IF NOT EXISTS xjw_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL UNIQUE,
    room_name TEXT NOT NULL,
    anchor_name TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT, -- JSON数组格式存储
    is_online BOOLEAN NOT NULL DEFAULT 0,
    viewer_count INTEGER NOT NULL DEFAULT 0,
    last_check_time TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 审核任务表
CREATE TABLE IF NOT EXISTS audit_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_date TEXT NOT NULL, -- YYYY-MM-DD格式
    shift_type TEXT NOT NULL, -- morning, afternoon, night
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    total_rooms INTEGER NOT NULL DEFAULT 0,
    reviewed_rooms INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    work_duration INTEGER NOT NULL DEFAULT 0, -- 分钟
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 违规记录表
CREATE TABLE IF NOT EXISTS violation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL, -- pornographic, gambling, fraud, violence, political, copyright, other
    severity INTEGER NOT NULL DEFAULT 1, -- 1-5级，5为最严重
    description TEXT NOT NULL,
    evidence_urls TEXT, -- JSON数组格式存储
    handled_by INTEGER,
    handled_at TIMESTAMP,
    handling_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES audit_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES xjw_rooms(id),
    FOREIGN KEY (handled_by) REFERENCES users(id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_parent_id ON departments(parent_id);

CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_employee_id ON employees(employee_id);
CREATE INDEX IF NOT EXISTS idx_employees_work_status ON employees(work_status);

CREATE INDEX IF NOT EXISTS idx_xjw_rooms_room_id ON xjw_rooms(room_id);
CREATE INDEX IF NOT EXISTS idx_xjw_rooms_category ON xjw_rooms(category);
CREATE INDEX IF NOT EXISTS idx_xjw_rooms_is_online ON xjw_rooms(is_online);

CREATE INDEX IF NOT EXISTS idx_audit_tasks_user_id ON audit_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_tasks_task_date ON audit_tasks(task_date);
CREATE INDEX IF NOT EXISTS idx_audit_tasks_shift_type ON audit_tasks(shift_type);
CREATE INDEX IF NOT EXISTS idx_audit_tasks_status ON audit_tasks(status);

CREATE INDEX IF NOT EXISTS idx_violation_records_task_id ON violation_records(task_id);
CREATE INDEX IF NOT EXISTS idx_violation_records_room_id ON violation_records(room_id);
CREATE INDEX IF NOT EXISTS idx_violation_records_violation_type ON violation_records(violation_type);
CREATE INDEX IF NOT EXISTS idx_violation_records_severity ON violation_records(severity);
CREATE INDEX IF NOT EXISTS idx_violation_records_handled_by ON violation_records(handled_by);

-- 创建触发器自动更新updated_at字段
CREATE TRIGGER IF NOT EXISTS update_users_updated_at
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_departments_updated_at
AFTER UPDATE ON departments
BEGIN
    UPDATE departments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_employees_updated_at
AFTER UPDATE ON employees
BEGIN
    UPDATE employees SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_xjw_rooms_updated_at
AFTER UPDATE ON xjw_rooms
BEGIN
    UPDATE xjw_rooms SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_audit_tasks_updated_at
AFTER UPDATE ON audit_tasks
BEGIN
    UPDATE audit_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_violation_records_updated_at
AFTER UPDATE ON violation_records
BEGIN
    UPDATE violation_records SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;