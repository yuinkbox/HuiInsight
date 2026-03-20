# AHDUNYI Terminal PRO

> **企业级直播内容风控审核桌面终端** — Python 后端驱动 Vue 3 前端，打包为独立 Windows EXE。

---

## 项目概览

AHDUNYI Terminal PRO 是面向直播平台风控团队的专用桌面客户端。它将 Arco Design 驱动的 Vue 3 Web 前端嵌入 PyQt6 WebEngine 窗口，通过 QWebChannel 实现 Python 与 JavaScript 的双向通信，并借助 Windows UIAutomation 实现对目标巡查进程的无侵入房间监控。

```
┌─────────────────────────────────────────────────────┐
│               AHDUNYI Terminal PRO                  │
│  ┌───────────────────────────────────────────────┐  │
│  │   QWebEngineView  (Vue 3 + Arco Design SPA)   │  │
│  │   LoginPage → Dashboard → 各角色专属视图       │  │
│  │   实时巡查 | 违规审核 | SOP标准 | 影子审计大屏   │  │
│  └────────────────┬──────────────────────────────┘  │
│                   │  QWebChannel (AppBridge)         │
│  ┌────────────────▼──────────────────────────────┐  │
│  │  Python 后端                                   │  │
│  │  ConfigManager | RoomMonitor | NetworkClient   │  │
│  │  BehaviorAnalyzer | FileHelper | Logging       │  │
│  └───────────────────────────────────────────────┘  │
│                   │  HTTP / REST                     │
│          阿里云生产服务器 106.15.32.246:8000            │
└─────────────────────────────────────────────────────┘
```

---

## 核心功能

| 模块 | 描述 |
|------|------|
| 登录鉴权 | JWT Token，角色路由守卫（审核员 / 组长 / 主管） |
| 实时巡查 | SSE 推流，实时展示在线巡查任务 |
| 违规审核 | 列表检索、违规定性、证据归档 |
| SOP 标准 | 红线标准与业务规则浏览 |
| 影子审计大屏 | 主管专属：实时房间监控状态与审计统计 |
| 班次调度 | 组长视图：按班次日期分配任务 |
| RBAC 管理 | 主管在线修改成员角色，查看团队洞察 |
| RoomMonitor | Windows UIAutomation 无侵入读取目标进程房间 ID |
| AppBridge | QWebChannel 双向桥接：Python 状态实时推送至前端 |

---

## 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| Vue 3 + TypeScript | 核心框架，Composition API |
| Arco Design Vue | 字节跳动企业级 UI 组件库 |
| Vite 5 | 构建工具 |
| Vue Router 4 | 路由 + 角色权限守卫 |
| Pinia | 状态管理 |
| Axios | HTTP 客户端 |
| vue-tsc 3.x | Vue SFC TypeScript 类型检查 |

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.12+ | 运行时 |
| PyQt6 + WebEngine | GUI 框架 + Chromium 内嵌浏览器 |
| uiautomation | Windows UI 自动化（RoomMonitor） |
| psutil | 进程监控 |
| requests | HTTP 客户端 |
| cachetools | TTL 内存缓存 |
| PyInstaller | 打包为 Windows EXE |

---

## 项目结构

```
AHDUNYI_Terminal_PRO/
├── src/                        # Python 后端
│   ├── main.py                 # 应用入口 v9.0.0
│   ├── config/settings.py      # ConfigManager + AppSettings
│   ├── app/
│   │   ├── bridge/web_channel.py   # QWebChannel AppBridge
│   │   ├── core/room_monitor.py    # UIAutomation 房间监控
│   │   └── ui/                     # LoginWindow / MainWindow
│   └── utils/                  # 日志、HTTP 封装
│
├── web_client/                 # Vue 3 前端
│   └── src/
│       ├── api/                # Axios 接口层
│       ├── config/index.ts     # 环境配置
│       ├── layouts/            # 主布局
│       ├── router/index.ts     # 路由 + 守卫
│       └── views/              # 各页面
│
├── build/
│   ├── build.py               # 一键构建脚本
│   └── AHDUNYI.spec           # PyInstaller 规格
│
├── config.example.json        # 配置模板
├── requirements.txt
└── .gitignore
```

---

## 快速开始

### 环境要求

- Windows 10 / 11 x64
- Python 3.12+
- Node.js 18+ / npm 9+

### 1. 克隆仓库

```bash
git clone https://github.com/yuinkbox/AHDUNYI_Terminal_PRO.git
cd AHDUNYI_Terminal_PRO
```

### 2. 创建配置文件

```bash
copy config.example.json config.json
```

编辑 `config.json`，填入实际服务器地址：

```json
{
  "server": { "url": "http://YOUR_SERVER_IP:8000" }
}
```

### 3. 安装依赖

```bash
# Python
pip install -r requirements.txt

# 前端
cd web_client && npm install && cd ..
```

### 4. 运行（开发模式）

```bash
python src/main.py
# 或指定配置文件
python src/main.py config.json
```

---

## 一键打包 EXE

```bash
python build/build.py
```

自动步骤：
1. `npm run build` — 编译 Vue 前端
2. 清理旧版 PyInstaller 产物
3. 检查 Python 依赖
4. PyInstaller 打包
5. 输出报告

**产物路径：**

```
dist/AHDUNYI_Terminal_PRO/
├── AHDUNYI_Terminal_PRO.exe       # 主程序（~3.7 MB）
└── _internal/PyQt6/Qt6/bin/
    └── QtWebEngineProcess.exe     # Chromium 子进程（~0.7 MB）
```

---

## 配置说明

```jsonc
{
  "server": { "url": "http://106.15.32.246:8000" },
  "gui": { "window_width": 1440, "window_height": 900 },
  "room_monitor": {
    "target_process": "small_dimple.exe",
    "heartbeat_interval": 2.0,
    "max_search_depth": 8
  },
  "features": { "auto_start_monitor": true },
  "debug": { "enable_console": true }
}
```

---

## 用户角色

| 角色 | 标识 | 可访问模块 |
|------|------|------------|
| 审核员 | `auditor` | 工作台、实时巡查、违规审核、SOP |
| 组长 | `shift_leader` | 审核员全部 + 班次调度 |
| 主管 | `supervisor` | 全部 + 影子审计大屏、RBAC、系统设置 |

---

## 日志

运行日志保存至 `logs/client.log`（UTF-8，GBK 环境安全）。

---

## 架构原则

- **控制逻辑与 UI 分离**：Python 通过 QWebChannel 驱动前端，前端不直接操作系统资源
- **消除全局变量**：状态通过 `ConfigManager` / `AppBridge` / Pinia 集中管理
- **UTF-8 优先**：所有文件 UTF-8 编码，subprocess 强制 `encoding="utf-8"`，杜绝 Windows GBK 冲突
- **PEP 8**：全函数类型标注，标准 Docstrings

---

## 开发指南

```bash
# 前端热更新
cd web_client && npm run dev
# 访问 http://localhost:5173
```

Commit 规范遵循 Conventional Commits：`feat` / `fix` / `refactor` / `docs` / `chore`

---

## License

Copyright © 2026 AHDUNYI. All rights reserved.
