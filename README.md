# AHDUNYI Terminal PRO

直播内容巡查终端。PyQt6 壳体内嵌编译后的 Vue 3 前端，Python FastAPI 后端将班次指标持久化至 MySQL。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 桌面壳体 | Python 3.12 · PyQt6 · QWebEngineView · QWebChannel |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Arco Design |
| 后端 | FastAPI · SQLAlchemy 2 · Alembic · PyMySQL |
| 数据库 | MySQL 8（字符集 utf8mb4） |
| 鉴权 | JWT (python-jose) · bcrypt |
| CI/CD | GitHub Actions → 阿里云 ECS（SSH 部署） |
| 打包 | PyInstaller（单目录 EXE） |

---

## 目录结构

```
AHDUNYI_Terminal_PRO/
├── client/
│   ├── desktop/                  # PyQt6 应用
│   │   ├── app/
│   │   │   ├── bridge/           # QWebChannel ↔ Vue 通信桥
│   │   │   ├── core/             # 房间监测、内存探针、行为分析器
│   │   │   └── ui/               # 主窗口、登录窗口
│   │   ├── config/               # AppSettings 数据类 + JSON 加载器
│   │   ├── utils/
│   │   └── main.py               # 入口
│   ├── web/                      # Vue 3 前端
│   │   └── src/
│   │       ├── api/              # rbacApi、axios HTTP 层
│   │       ├── bridge/           # qt_channel.ts（QWebChannel 适配器）
│   │       ├── layouts/          # 主布局
│   │       ├── router/           # Vue Router（hash 模式，兼容 file://）
│   │       ├── stores/           # Pinia：permission、workflow、loading
│   │       └── views/            # 直播监测、工作概览等页面
│   └── build/                    # PyInstaller spec + 一键构建脚本
├── server/                       # FastAPI 应用
│   ├── api/                      # 路由：auth、tasks、team、users、logs、violation
│   ├── constants/                # 角色定义、权限矩阵
│   ├── core/                     # SQLAlchemy 引擎与会话工厂
│   ├── db/                       # ORM 模型、init_db 种子脚本
│   ├── schemas/                  # Pydantic 请求/响应模型
│   ├── services/                 # dispatch.py（最少分配优先算法）
│   ├── alembic/                  # 迁移历史
│   ├── main.py                   # FastAPI 应用工厂
│   ├── Dockerfile
│   └── requirements.txt
├── shared/                       # 跨层共享常量与 Schema
│   ├── constants/api_paths.py
│   ├── patterns/room_id.py
│   └── schemas/
├── config.json                   # 运行时配置：服务器地址、窗口尺寸、调试开关
├── db_schema.md                  # 数据库字段字典
└── .github/workflows/
    ├── server-deploy.yml         # 代码检查 → git pull → pip install → 重启服务
    └── client-build.yml
```

---

## API 一览

### 鉴权

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/login` | 用户名/密码 → 24 小时 JWT |
| GET | `/api/auth/permissions` | 重新水合前端权限 Store |
| POST | `/api/auth/change-password` | 修改当前用户密码 |

### 班次任务（`shift_tasks` 表）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/task/my/live-patrol` | 获取或自动创建今日直播巡查任务（幂等，无需派发） |
| GET | `/api/task/my` | 今日任务 + 历史任务 + 本周统计 |
| PATCH | `/api/task/{id}/progress` | 持久化 `reviewed_count`、`violation_count`、`work_duration`、`is_completed` |
| POST | `/api/task/{id}/complete` | 标记任务完成（`is_completed = 1`） |
| POST | `/api/dispatch/auto` | 最少分配优先批量派发（需 `action:dispatch_task` 权限） |

### 团队与审计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/team/insight` | 按日期范围、用户、渠道聚合统计 |
| GET | `/api/team/user/{id}/stats` | 单用户详细数据 |
| POST | `/api/log/action` | 追加细粒度操作日志 |
| GET | `/api/log/list` | 分页查询操作日志（需 `view:shadow_audit`） |

---

## 数据持久化链路

每次直播巡查会话对应 `shift_tasks` 中的一条记录。

```
审核员登录
    └─→ GET /api/task/my/live-patrol          # 不存在则自动创建（幂等）
            └─→ 接入工作流（前端计时器启动）
                    ├─→ PATCH …/progress  每 10 秒             # 定时增量同步
                    ├─→ PATCH …/progress  点击「挂起」时        # 强制落盘
                    ├─→ PATCH …/progress  路由离开时（beforeEach）# 防丢数据
                    └─→ PATCH …/progress  is_completed=true    # 结束工作流
```

时区：所有 `shift_date` 均以 **北京时间（UTC+8）** 写入与查询。

---

## 角色权限矩阵

| 角色 | 关键权限 |
|---|---|
| `manager` | 全部权限 + `view:shadow_audit`、`action:dispatch_task` |
| `team_leader` | `action:dispatch_task`、`view:shadow_audit` |
| `qa_specialist` | `view:violations`、`view:sop` |
| `auditor` | `view:realtime`、`view:sop` |

权限矩阵定义在服务端 `server/constants/permissions.py`，前端不做角色字符串硬编码。

---

## 快速启动

### 后端

```bash
cd server
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env              # 填写 DATABASE_URL、JWT_SECRET_KEY

# 执行数据库迁移
alembic upgrade head

# 初始化种子数据（首次运行）
python -m server.db.init_db

# 启动服务
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档：`http://localhost:8000/docs`

### 前端（开发模式）

```bash
cd client/web
npm install
npm run dev
```

### 桌面端打包

```bash
# 需要 Python 3.12 + Node.js 18+ 在 PATH 中
python client/build/build.py
# 输出：dist/AHDUNYI_Terminal_PRO/AHDUNYI_Terminal_PRO.exe
```

将 `config.json` 放置在 `.exe` 同级目录，可覆盖服务器地址与窗口尺寸。

---

## 运行时配置（`config.json`）

```jsonc
{
  "server":       { "url": "http://HOST:8000" },
  "gui":          { "window_width": 1440, "window_height": 900 },
  "room_monitor": { "target_process": "small_dimple.exe", "memory_probe_enabled": true },
  "debug":        { "enable_console": false }   // true 时启动 DevTools 窗口
}
```

---

## CI/CD 流程

- **`server-deploy.yml`** — 监听 `main` 分支 `server/**` 路径变更：flake8 代码检查 → SSH 连入阿里云 ECS → `git pull` → `pip install` → `systemctl restart ahdunyi-api`
- **`client-build.yml`** — 监听 `main` 分支 `client/**` 路径变更：构建 Vue 前端
