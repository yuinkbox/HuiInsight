-- 添加绩效统计表
-- 徽鉴HuiInsight - 小酒窝语音审核部门中台系统
-- @author xuyu

-- 绩效统计表
CREATE TABLE IF NOT EXISTS performance_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    period TEXT NOT NULL, -- YYYY-MM格式
    total_tasks INTEGER NOT NULL DEFAULT 0,
    completed_tasks INTEGER NOT NULL DEFAULT 0,
    total_rooms_reviewed INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    average_work_duration REAL NOT NULL DEFAULT 0.0, -- 分钟
    quality_score REAL NOT NULL DEFAULT 0.0, -- 0-100分
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, period)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_performance_stats_user_id ON performance_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_stats_period ON performance_stats(period);
CREATE INDEX IF NOT EXISTS idx_performance_stats_quality_score ON performance_stats(quality_score);

-- 创建触发器自动更新updated_at字段
CREATE TRIGGER IF NOT EXISTS update_performance_stats_updated_at
AFTER UPDATE ON performance_stats
BEGIN
    UPDATE performance_stats SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 创建视图：部门绩效统计
CREATE VIEW IF NOT EXISTS department_performance AS
SELECT 
    d.id as department_id,
    d.name as department_name,
    d.code as department_code,
    p.period,
    COUNT(DISTINCT p.user_id) as employee_count,
    SUM(p.total_tasks) as total_tasks,
    SUM(p.completed_tasks) as completed_tasks,
    SUM(p.total_rooms_reviewed) as total_rooms_reviewed,
    SUM(p.violation_count) as total_violations,
    AVG(p.average_work_duration) as avg_work_duration,
    AVG(p.quality_score) as avg_quality_score
FROM performance_stats p
JOIN employees e ON p.user_id = e.user_id
JOIN departments d ON e.department_id = d.id
GROUP BY d.id, d.name, d.code, p.period;

-- 创建视图：员工月度绩效排名
CREATE VIEW IF NOT EXISTS employee_monthly_ranking AS
SELECT 
    p.id,
    p.user_id,
    u.display_name,
    e.employee_id,
    e.position,
    d.name as department_name,
    p.period,
    p.total_tasks,
    p.completed_tasks,
    p.total_rooms_reviewed,
    p.violation_count,
    p.average_work_duration,
    p.quality_score,
    RANK() OVER (PARTITION BY p.period ORDER BY p.quality_score DESC) as quality_rank,
    RANK() OVER (PARTITION BY p.period ORDER BY p.completed_tasks DESC) as productivity_rank
FROM performance_stats p
JOIN users u ON p.user_id = u.id
JOIN employees e ON p.user_id = e.user_id
JOIN departments d ON e.department_id = d.id
WHERE u.is_active = 1 AND e.work_status = '在职';

-- 创建视图：违规类型统计
CREATE VIEW IF NOT EXISTS violation_type_statistics AS
SELECT 
    v.violation_type,
    COUNT(*) as count,
    AVG(v.severity) as avg_severity,
    strftime('%Y-%m', v.created_at) as month,
    d.name as department_name
FROM violation_records v
JOIN audit_tasks a ON v.task_id = a.id
JOIN users u ON a.user_id = u.id
JOIN employees e ON u.id = e.user_id
JOIN departments d ON e.department_id = d.id
GROUP BY v.violation_type, strftime('%Y-%m', v.created_at), d.name;

-- 创建视图：审核任务完成情况
CREATE VIEW IF NOT EXISTS audit_task_completion AS
SELECT 
    a.task_date,
    a.shift_type,
    COUNT(*) as total_tasks,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    SUM(CASE WHEN a.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
    SUM(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending_tasks,
    SUM(a.reviewed_rooms) as total_rooms_reviewed,
    SUM(a.violation_count) as total_violations,
    AVG(a.work_duration) as avg_work_duration
FROM audit_tasks a
GROUP BY a.task_date, a.shift_type;

-- 插入初始部门数据
INSERT OR IGNORE INTO departments (name, code, description) VALUES
('审核一部', 'AUDIT_001', '主要负责小酒窝语音平台日常审核'),
('审核二部', 'AUDIT_002', '主要负责小酒窝语音平台专项审核'),
('质量监控部', 'QUALITY_001', '负责审核质量监控和绩效评估'),
('技术支持部', 'TECH_001', '负责系统维护和技术支持');

-- 插入初始管理员用户（密码：admin123，实际使用中应该使用加密密码）
INSERT OR IGNORE INTO users (username, display_name, email, password_hash, role, is_active) VALUES
('admin', '系统管理员', 'admin@huijian.com', '$2b$12$YourEncryptedPasswordHashHere', 'admin', 1),
('supervisor1', '主管张三', 'supervisor1@huijian.com', '$2b$12$YourEncryptedPasswordHashHere', 'supervisor', 1),
('auditor1', '审核员李四', 'auditor1@huijian.com', '$2b$12$YourEncryptedPasswordHashHere', 'auditor', 1);

-- 插入初始员工数据
INSERT OR IGNORE INTO employees (user_id, department_id, employee_id, position, join_date, work_status) VALUES
(1, 4, 'TECH001', '系统管理员', '2024-01-01', '在职'),
(2, 3, 'QUALITY001', '质量主管', '2024-01-01', '在职'),
(3, 1, 'AUDIT001', '高级审核员', '2024-01-01', '在职');