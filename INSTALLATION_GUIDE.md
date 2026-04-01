# 徽鉴HuiInsight - 安装和测试指南

## 项目概述
徽鉴HuiInsight是一个专门为审核部门设计的内部中台系统，用于管理"小酒窝语音"平台的审核工作。项目采用Tauri+React技术栈，实现跨平台桌面应用。

## 📦 安装包状态

### 当前状态
由于构建环境配置问题（缺少Visual C++构建工具），完整的Tauri安装包暂时无法生成。但项目已准备好以下测试方案：

### 可用的测试方案

#### 方案1：开发环境运行（推荐）
```bash
# 1. 克隆项目
git clone https://github.com/yuinkbox/HuiInsight.git
cd HuiInsight

# 2. 安装前端依赖
cd tauri-app
npm install

# 3. 运行开发环境
npm run tauri dev
```

#### 方案2：命令行测试版本
```bash
# 运行命令行测试程序
cd HuiInsight\test_cli
cargo run
```

## 🔧 系统要求

### 开发环境
- **操作系统**: Windows 10/11
- **Node.js**: 18.x 或更高版本
- **Rust**: 1.70 或更高版本
- **Git**: 版本控制工具

### 运行环境
- **操作系统**: Windows 10/11
- **内存**: 4GB 或更高
- **存储空间**: 500MB 可用空间

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装Node.js
# 下载地址: https://nodejs.org/

# 安装Rust
# 下载地址: https://rustup.rs/

# 安装Git
# 下载地址: https://git-scm.com/
```

### 2. 项目设置
```bash
# 克隆项目
git clone https://github.com/yuinkbox/HuiInsight.git
cd HuiInsight

# 查看项目结构
tree /F
```

### 3. 运行开发环境
```bash
# 进入Tauri应用目录
cd tauri-app

# 安装依赖
npm install

# 启动开发服务器
npm run tauri dev
```

## 📊 核心功能测试

### 已实现的功能
1. ✅ **用户认证系统**
   - JWT令牌认证
   - 四级角色权限（管理员、主管、审核员、普通用户）
   - 密码安全哈希（Argon2算法）

2. ✅ **审核任务管理**
   - 今日任务自动创建
   - 任务进度跟踪
   - 周度统计报表

3. ✅ **数据库系统**
   - SQLite本地存储
   - 7个核心数据表
   - 自动迁移脚本

4. ✅ **配置管理**
   - 环境变量支持
   - 配置文件管理
   - 错误处理系统

### 测试方法
```bash
# 测试数据库连接
cd test_cli
cargo run

# 预期输出：
# === 徽鉴HuiInsight 命令行测试版本 ===
# 1. 测试数据库连接... ✓
# 2. 测试数据模型... ✓
# 3. 测试核心功能... ✓
```

## 🛠️ 构建问题解决

### 已知问题
1. **Visual C++构建工具缺失**
   - 症状: `link.exe not found` 错误
   - 解决方案: 安装Visual Studio Build Tools

2. **Tauri版本兼容性**
   - 症状: 特性匹配错误
   - 解决方案: 已更新到兼容版本

3. **项目名称编码**
   - 症状: 中文字符路径问题
   - 解决方案: 已改为英文名称

### 临时解决方案
```bash
# 使用开发模式运行
npm run tauri dev

# 或使用测试版本
cd test_cli
cargo run
```

## 📁 项目结构

```
HuiInsight/
├── tauri-app/                    # Tauri桌面应用
│   ├── src-tauri/               # Rust后端
│   │   ├── commands/            # Tauri Commands
│   │   ├── database/            # 数据库模块
│   │   └── migrations/          # 数据库迁移
│   ├── src/types/               # TypeScript类型定义
│   └── 配置文件
├── test_cli/                    # 命令行测试版本
├── PROGRESS_SUMMARY.md          # 项目进度总结
└── INSTALLATION_GUIDE.md        # 本安装指南
```

## 🔍 功能验证

### 数据库验证
```sql
-- 检查数据库结构
SELECT name FROM sqlite_master WHERE type='table';

-- 预期结果：
-- users
-- departments
-- employees
-- xjw_rooms
-- audit_tasks
-- violation_records
-- performance_stats
```

### API验证
```bash
# 启动开发服务器后，测试API
# 1. 用户登录
# 2. 获取今日任务
# 3. 更新任务进度
# 4. 获取统计信息
```

## 🎯 下一步计划

### 短期目标（1-2周）
1. **前端界面开发**
   - 登录页面
   - 主仪表板
   - 审核任务界面

2. **构建环境修复**
   - 安装Visual C++构建工具
   - 生成完整安装包

### 中期目标（2-4周）
1. **完整功能实现**
   - 实时房间监控
   - 违规管理
   - 报表生成

2. **系统优化**
   - 性能优化
   - 用户体验改进
   - 测试用例编写

## 📞 技术支持

### 常见问题
1. **Q: 无法启动开发环境**
   A: 检查Node.js和Rust安装，确保版本兼容

2. **Q: 数据库连接失败**
   A: 检查文件权限，确保有读写权限

3. **Q: 构建失败**
   A: 安装Visual Studio Build Tools

### 联系方式
- **项目仓库**: https://github.com/yuinkbox/HuiInsight
- **项目作者**: xuyu
- **项目状态**: 基础架构完成，前端界面待开发

## 📈 项目状态总结

### 已完成（100%）
- ✅ 项目架构设计
- ✅ 数据库系统
- ✅ 用户认证
- ✅ 任务管理
- ✅ 配置管理

### 待完成（0%）
- ⏳ 前端界面
- ⏳ 安装包生成
- ⏳ 用户文档

### 当前重点
**前端界面开发** - 将已实现的后端功能通过React界面呈现

## 🚨 重要提醒

1. **生产环境**: 当前为开发版本，不建议用于生产环境
2. **数据安全**: 生产环境需要修改JWT密钥和数据库配置
3. **备份策略**: 定期备份SQLite数据库文件
4. **更新策略**: 关注GitHub仓库获取最新更新

---

**最后更新**: 2026-03-31  
**版本**: v0.1.0 (开发版)  
**状态**: 基础功能完成，可进行开发测试