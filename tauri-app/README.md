# 徽鉴HuiInsight

Windows桌面直播内容巡查终端

## 项目简介

徽鉴HuiInsight是一款专业的Windows桌面应用，用于直播内容巡查和违规检测。应用采用Tauri + React + TypeScript技术栈开发，提供高效、稳定的巡查工作体验。

## 技术栈

- **桌面框架**: Tauri (Rust + WebView)
- **前端框架**: React 18 + TypeScript
- **UI组件库**: Semi Design
- **状态管理**: Zustand
- **本地数据库**: SQLite
- **构建工具**: Vite
- **包管理**: pnpm

## 功能特性

### 核心功能
- 用户认证和权限管理
- 直播房间实时监控
- 违规内容检测和记录
- 工作流任务管理
- 数据统计和报表生成

### 系统特性
- Windows原生集成
- 系统托盘支持
- 全局快捷键
- 自动更新机制
- 离线工作支持

## 开发环境

### 必需工具
1. **Rust工具链**: `rustup install stable`
2. **Node.js**: 18.x LTS版本
3. **pnpm**: `npm install -g pnpm`
4. **Visual Studio Build Tools** (Windows必需)

### 推荐VS Code扩展
- Rust Analyzer
- TypeScript/JavaScript扩展
- ESLint
- Prettier
- GitLens

## 快速开始

### 安装依赖
```bash
pnpm install
```

### 开发模式
```bash
pnpm tauri dev
```

### 生产构建
```bash
pnpm tauri build
```

### 代码检查
```bash
pnpm lint
pnpm type-check
```

## 项目结构

```
徽鉴HuiInsight/
├── src-tauri/          # Rust后端代码
│   ├── src/commands/   # Tauri Commands
│   ├── src/database/   # 数据库模块
│   └── src/services/   # 业务服务
├── src/                # React前端代码
│   ├── components/     # 可复用组件
│   ├── pages/         # 页面组件
│   ├── stores/        # 状态管理
│   └── services/      # 前端服务
└── tests/             # 测试文件
```

## 开发规范

### 代码风格
- 使用TypeScript严格模式
- 遵循ESLint和Prettier配置
- 组件使用函数式组件和Hooks
- 状态管理使用Zustand

### 提交规范
- 使用Conventional Commits规范
- 提交前运行代码检查和测试
- 保持提交信息清晰明确

### 测试要求
- 核心功能必须有单元测试
- 公共组件必须有测试用例
- 保持测试覆盖率在80%以上

## 构建和发布

### 开发构建
```bash
pnpm tauri build --debug
```

### 生产构建
```bash
pnpm tauri build
```

### 创建安装包
```bash
pnpm tauri build --bundles nsis
```

## 文档

- [架构设计](./docs/architecture/README.md)
- [API文档](./docs/api/README.md)
- [部署指南](./docs/deployment/README.md)
- [开发指南](./docs/development/README.md)

## 许可证

本项目采用MIT许可证。详见[LICENSE](./LICENSE)文件。

## 作者

xuyu

## 支持

如有问题或建议，请提交Issue或联系作者。