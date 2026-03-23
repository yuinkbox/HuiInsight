# 测试环境验证指南

## 🎉 当前状态

✅ **测试环境已成功部署并运行**
- 地址：http://122.51.72.36:8002
- 状态：服务正常运行
- 健康检查：✅ 通过
- API文档：✅ 可访问
- 数据库连接：✅ 正常

## 🔧 待修复问题

⚠️ **systemd服务配置问题**
- 问题：Python路径配置错误
- 当前路径：`/root/.openclaw/workspace/AHDUNYI_Terminal_PRO`
- 配置路径：`/app/AHDUNYI_Terminal_PRO`（错误）
- 影响：systemd服务无法启动，但手动启动的服务正常运行

## 📋 验证步骤

### 1. 基础连接测试
```bash
# 健康检查
curl http://122.51.72.36:8002/health
# 预期：{"status":"ok","version":"9.1.0","environment":"test"}

# API文档
curl http://122.51.72.36:8002/docs
# 预期：返回Swagger UI页面

# 根目录
curl http://122.51.72.36:8002/
# 预期：{"service":"AHDUNYI Terminal PRO","environment":"test","status":"running"}
```

### 2. 功能接口测试
```bash
# 登录接口测试（需要有效用户）
curl -X POST http://122.51.72.36:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
# 预期：返回JWT令牌或401错误

# 权限接口测试
curl http://122.51.72.36:8002/api/auth/permissions
# 预期：需要认证，返回401
```

### 3. 数据库连接测试
```bash
# 在服务器上测试数据库连接
cd /root/.openclaw/workspace/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
python -c "
from server.core.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

## 🚀 客户端测试

### 1. 配置检查
确保 `config.json` 中的服务器地址正确：
```json
{
  "server": {
    "url": "http://122.51.72.36:8002"
  }
}
```

### 2. 打包EXE
```bash
# 在本地开发环境
python client/build/build.py
```

### 3. 测试登录
1. 运行生成的EXE文件
2. 输入测试账号密码
3. 验证是否成功登录

### 4. 功能测试
- ✅ 登录认证
- ✅ 权限加载
- ✅ 任务管理
- ✅ 房间监控（如果配置了桌面客户端）

## 🔧 systemd修复方案

### 方案A：立即修复（推荐）
发送 `QUICK_FIX_SYSTEMD.txt` 给openclaw执行。

### 方案B：使用模板部署
```bash
# 在服务器上执行
cd /root/.openclaw/workspace/AHDUNYI_Terminal_PRO/server

# 使用模板生成服务配置
sed -e "s|{PROJECT_PATH}|/root/.openclaw/workspace/AHDUNYI_Terminal_PRO|g" \
    -e "s|{ENVIRONMENT}|test|g" \
    -e "s|{PORT}|8002|g" \
    ahdunyi-api.service.template > /etc/systemd/system/ahdunyi-test-api.service

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable ahdunyi-test-api
sudo systemctl start ahdunyi-test-api
```

### 方案C：保持现状
如果systemd修复复杂，可以：
1. 保持当前手动启动的服务
2. 使用screen或nohup保持服务运行
3. 添加监控脚本确保服务异常时自动重启

## 📊 成功标准

### 基础标准（已满足）
1. ✅ 服务可访问：http://122.51.72.36:8002
2. ✅ 健康检查通过：返回成功状态
3. ✅ API文档可访问：Swagger UI正常显示
4. ✅ 数据库连接正常：无连接错误

### 进阶标准（待验证）
1. 🔄 systemd服务正常运行：`systemctl status` 显示 active
2. 🔄 客户端EXE可连接：成功登录测试环境
3. 🔄 所有API接口可用：无500错误
4. 🔄 权限系统正常：不同角色看到不同界面

## 🛠️ 故障排除

### 如果客户端连接失败
1. **检查网络**：确保客户端可以访问 `122.51.72.36:8002`
2. **检查防火墙**：确保腾讯云安全组开放8002端口
3. **检查配置**：确认 `config.json` 中的服务器地址正确
4. **查看日志**：检查服务器日志中的错误信息

### 如果API返回错误
1. **查看服务日志**：`journalctl -u ahdunyi-test-api` 或直接查看服务输出
2. **检查数据库**：确认MySQL服务运行正常
3. **检查环境变量**：确认 `.env` 文件配置正确
4. **检查依赖**：确认所有Python包已正确安装

### 如果权限问题
1. **检查用户表**：确认测试用户存在且激活
2. **检查角色权限**：确认用户角色有相应权限
3. **检查JWT配置**：确认JWT密钥和算法配置正确

## 📈 监控建议

### 基础监控
```bash
# 服务状态监控
sudo systemctl status ahdunyi-test-api

# 日志监控
sudo journalctl -u ahdunyi-test-api -f

# 连接监控
watch -n 5 "curl -s http://122.51.72.36:8002/health | jq .status"
```

### 性能监控
1. **CPU/内存使用**：`top` 或 `htop`
2. **网络连接**：`netstat -tlnp | grep :8002`
3. **数据库连接**：MySQL监控工具

## 🎯 下一步行动

### 立即行动
1. ✅ 发送systemd修复指令给openclaw
2. 🔄 等待openclaw执行并报告结果
3. 🔄 测试客户端EXE连接
4. 🔄 验证所有API功能

### 长期优化
1. 完善测试环境CI/CD流程
2. 添加自动化测试脚本
3. 设置监控告警
4. 定期备份测试数据

## 📞 支持信息

**服务器信息**
- 地址：122.51.72.36:8002
- 路径：/root/.openclaw/workspace/AHDUNYI_Terminal_PRO
- 数据库：MySQL @ 127.0.0.1:3306

**联系人**
- 服务器运维：openclaw
- 开发支持：yuinkbox
- 测试验证：前端团队

**文档链接**
- API文档：http://122.51.72.36:8002/docs
- 健康检查：http://122.51.72.36:8002/health
- 项目代码：https://github.com/yuinkbox/AHDUNYI_Terminal_PRO