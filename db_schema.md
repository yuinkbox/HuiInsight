# HuiInsight (徽鉴) 终端后端数据库结构字典

**数据库名称：** `ahdunyi_pro_db`
**数据库类型：** MySQL

---

## 1. 核心业务表结构总览

### 1.1 `users` (用户权限与组织架构表)
| 字段 | 类型 | 是否为空 | 键 | 默认值 | 说明 |
|------|------|----------|----|--------|------|
| id | int | NO | PRI | NULL | 主键，自增 |
| username | varchar(64) | NO | UNI | NULL | 用户名，唯一索引 |
| full_name | varchar(128) | NO | | NULL | 全名 |
| hashed_password | varchar(255) | NO | | NULL | 哈希密码 |
| is_superuser | tinyint(1) | NO | | NULL | 是否超级用户 |
| role | enum | NO | | NULL | 角色：manager, team_leader, qa_specialist, admin_support, auditor |
| is_active | tinyint(1) | NO | | NULL | 是否激活 |
| email | varchar(128) | YES | | NULL | 邮箱 |
| created_at | datetime | NO | | now() | 创建时间 |
| updated_at | datetime | YES | | NULL | 更新时间 |

**索引：**
* PRIMARY (id)
* username (唯一索引)
* ix_users_username (username)


### 1.2 `shift_tasks` (班次任务与宏观指标表)
| 字段 | 类型 | 是否为空 | 键 | 默认值 | 说明 |
|------|------|----------|----|--------|------|
| id | int | NO | PRI | NULL | 主键，自增 |
| user_id | int | NO | MUL | NULL | 用户ID (关联 users.id) |
| shift_date | varchar(10) | NO | MUL | NULL | 班次日期 (如 YYYY-MM-DD) |
| shift_type | varchar(16) | NO | | NULL | 班次类型 |
| task_channel | varchar(16) | NO | | NULL | 任务渠道 |
| is_completed | tinyint(1) | NO | | NULL | 是否完成 (0=进行中, 1=已结束) |
| reviewed_count | int | NO | | NULL | 审核次数 |
| violation_count | int | NO | | NULL | 违规次数 |
| work_duration | int | NO | | NULL | 工作时长 |
| created_at | datetime | NO | | now() | 创建时间 |
| updated_at | datetime | YES | | NULL | 更新时间 |

**索引：**
* PRIMARY (id)
* ix_shift_tasks_user_date (user_id, shift_date)
* ix_shift_tasks_user_id (user_id)
* ix_shift_tasks_date_type (shift_date, shift_type)


### 1.3 `action_logs` (细颗粒度操作追溯表)
| 字段 | 类型 | 是否为空 | 键 | 默认值 | 说明 |
|------|------|----------|----|--------|------|
| id | int | NO | PRI | NULL | 主键，自增 |
| user_id | int | NO | MUL | NULL | 用户ID (关联 users.id) |
| username | varchar(64) | NO | | NULL | 用户名 |
| action | varchar(64) | NO | MUL | NULL | 操作类型 (如 切房审查, 违规处置等) |
| details | text | NO | | NULL | 操作详情 |
| task_id | int | YES | | NULL | 任务ID (关联 shift_tasks.id) |
| duration | int | YES | | NULL | 持续时间 |
| timestamp | datetime | NO | MUL | now() | 时间戳 |

**索引：**
* PRIMARY (id)
* ix_action_logs_timestamp (timestamp)
* ix_action_logs_user_ts (user_id, timestamp)
* ix_action_logs_action (action)
* ix_action_logs_user_id (user_id)

---

## 2. 实体关联关系 (ER Diagram)

1. **`users` ↔ `shift_tasks`**: 一对多。通过 `shift_tasks.user_id = users.id` 关联。
2. **`users` ↔ `action_logs`**: 一对多。通过 `action_logs.user_id = users.id` 关联。
3. **`shift_tasks` ↔ `action_logs`**: 一对多。通过 `action_logs.task_id = shift_tasks.id` 关联。

---
*注：请在 AI 代码生成过程中，严格参照上述字段名称、类型及枚举值进行开发，特别是状态拦截相关的 `is_completed` 字段校验。*
