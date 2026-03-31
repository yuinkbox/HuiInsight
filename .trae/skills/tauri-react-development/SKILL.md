---
name: "tauri-react-development"
description: "使用Tauri+React+TypeScript+Semi Design技术栈开发桌面应用。Invoke when developing desktop applications with Tauri, React 18, TypeScript, Semi Design, Rust Tauri Commands, and SQLite."
---

# Tauri+React开发技能

## 概述
此技能专门用于使用Tauri+React技术栈开发桌面应用程序。技能涵盖从项目初始化到部署的完整开发流程，特别针对直播内容巡查终端这类业务应用。

## 技术栈
- **桌面端框架**: Tauri (Rust + WebView)
- **前端框架**: React 18 + TypeScript
- **UI组件库**: Semi Design
- **状态管理**: React Context / Zustand / Jotai
- **本地存储**: SQLite (通过Tauri Commands访问)
- **构建工具**: Vite
- **包管理**: pnpm / npm

## 使用场景
- 开发跨平台桌面应用程序
- 需要本地数据存储和离线功能的桌面应用
- 需要高性能原生能力的Web应用
- 直播内容巡查、监控类桌面应用

## 核心功能

### 1. Tauri项目初始化
- 创建Tauri + React项目结构
- 配置Rust后端和React前端
- 设置开发环境和构建配置

### 2. React组件开发
- 使用TypeScript开发类型安全的React组件
- 集成Semi Design UI组件库
- 实现响应式布局和主题系统

### 3. Tauri Commands开发
- 编写Rust Tauri Commands处理业务逻辑
- 实现文件系统访问、系统通知等原生功能
- 开发SQLite数据库操作接口

### 4. 本地数据管理
- 使用SQLite进行本地数据存储
- 实现数据同步和缓存机制
- 处理离线数据队列

### 5. 前后端通信
- 通过Tauri Commands进行前后端通信
- 实现事件系统和消息传递
- 处理异步操作和错误处理

### 6. 打包和部署
- 配置多平台打包（Windows、macOS、Linux）
- 代码签名和发布流程
- 自动更新机制

## 工作流程

### 阶段1：项目初始化
1. 创建Tauri项目：`cargo tauri init`
2. 配置React + TypeScript前端
3. 安装和配置Semi Design
4. 设置开发环境

### 阶段2：架构设计
1. 设计应用目录结构
2. 规划React组件层次
3. 设计Tauri Commands接口
4. 设计SQLite数据库模式

### 阶段3：核心功能开发
1. 开发用户认证模块
2. 实现实时监控功能
3. 开发数据统计和报表
4. 实现系统设置和配置

### 阶段4：优化和测试
1. 性能优化和内存管理
2. 跨平台兼容性测试
3. 安全性和稳定性测试
4. 用户体验优化

### 阶段5：打包发布
1. 配置打包参数
2. 代码签名和公证
3. 发布到应用商店
4. 设置自动更新

## 最佳实践

### 1. 项目结构
```
src-tauri/          # Rust后端代码
  src/
    commands.rs     # Tauri Commands
    main.rs         # 主入口
    lib.rs          # 库代码
  Cargo.toml        # Rust依赖配置
  tauri.conf.json   # Tauri配置

src/                # React前端代码
  components/       # React组件
  pages/           # 页面组件
  hooks/           # 自定义Hooks
  stores/          # 状态管理
  utils/           # 工具函数
  types/           # TypeScript类型定义
  assets/          # 静态资源
```

### 2. Tauri Commands设计原则
- 每个Command职责单一
- 使用Result类型处理错误
- 添加适当的日志记录
- 考虑安全性（权限检查）

### 3. React组件设计
- 使用函数组件和Hooks
- 实现组件组合和复用
- 添加适当的类型定义
- 实现错误边界

### 4. 状态管理策略
- 本地状态使用useState/useReducer
- 全局状态使用Context或状态管理库
- 持久化状态使用SQLite
- 考虑状态同步和冲突解决

### 5. 性能优化
- 使用React.memo和useMemo优化渲染
- 实现虚拟列表处理大量数据
- 使用Web Workers处理计算密集型任务
- 优化图片和资源加载

## 常见模式

### 1. 数据库操作模式
```rust
// Rust Tauri Command示例
#[tauri::command]
async fn get_users(db: State<'_, DbConnection>) -> Result<Vec<User>, String> {
    let users = db.get_users().await.map_err(|e| e.to_string())?;
    Ok(users)
}
```

### 2. 前端调用模式
```typescript
// React组件中调用Tauri Command
const { invoke } = useTauri();
const users = await invoke<Array<User>>('get_users');
```

### 3. 错误处理模式
```typescript
try {
  const result = await invoke('some_command');
} catch (error) {
  console.error('Command failed:', error);
  // 显示用户友好的错误信息
}
```

## 工具和资源

### 开发工具
- **IDE**: VS Code with Rust and TypeScript extensions
- **调试**: Chrome DevTools for frontend, Rust debugger for backend
- **测试**: Jest for frontend, cargo test for Rust
- **构建**: GitHub Actions for CI/CD

### 学习资源
- Tauri官方文档：https://tauri.app/
- React官方文档：https://react.dev/
- TypeScript手册：https://www.typescriptlang.org/docs/
- Semi Design文档：https://semi.design/

## 成功指标
- 应用启动时间 < 3秒
- 内存占用 < 200MB
- 跨平台兼容性良好
- 用户操作响应时间 < 100ms
- 崩溃率 < 0.1%