# 测试环境问题修复指南

## 问题诊断结果

经过全面分析，发现测试环境存在以下问题：

### 1. **核心问题：后端服务未正确运行**
- 腾讯云服务器地址：`http://122.51.72.36:8002`
- 端口8002开放，但返回502错误
- 说明Nginx/负载均衡器正在运行，但后端FastAPI服务未启动或配置错误

### 2. **部署流程缺失**
- GitHub Actions只部署到阿里云（生产环境）
- develop分支的CI/CD流程只做代码检查，不部署
- 腾讯云服务器需要手动部署或新的自动部署流程

### 3. **配置不一致**
- `config.json`正确指向腾讯云服务器
- 前端配置默认使用`localhost:8000`
- 缺少测试环境专用的配置文件

## 修复步骤

### 第一步：在腾讯云服务器上手动部署

#### 1.1 登录腾讯云服务器
```bash
ssh root@122.51.72.36
```

#### 1.2 检查当前服务状态
```bash
# 检查是否有相关服务在运行
systemctl list-units | grep ahdunyi

# 检查端口占用
netstat -tlnp | grep :8002

# 检查Nginx配置（如果有）
nginx -t
```

#### 1.3 停止现有错误服务
```bash
# 如果有错误的服务，先停止
systemctl stop ahdunyi-api  # 停止可能错误的生产环境服务
```

#### 1.4 设置项目目录
```bash
cd /app
git clone https://github.com/yuinkbox/AHDUNYI_Terminal_PRO.git
cd AHDUNYI_Terminal_PRO
git checkout develop
```

#### 1.5 创建测试环境配置文件
```bash
# 创建.env文件
cat > server/.env << 'EOF'
ENVIRONMENT=test
DATABASE_URL=mysql+pymysql://ahdunyi_superyu:YOUR_TEST_DB_PASSWORD@localhost:3306/ahdunyi_test_db?charset=utf8mb4
JWT_SECRET_KEY=test-jwt-secret-key-change-for-security
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
SERVER_HOST=0.0.0.0
SERVER_PORT=8002
DEBUG=true
EOF

# 注意：将YOUR_TEST_DB_PASSWORD替换为实际的测试数据库密码
# 将localhost替换为腾讯云MySQL的实际IP地址
```

#### 1.6 设置Python虚拟环境和依赖
```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 1.7 设置systemd服务
```bash
# 复制服务配置文件
sudo cp ahdunyi-test-api.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable ahdunyi-test-api

# 启动服务
sudo systemctl start ahdunyi-test-api

# 检查服务状态
sudo systemctl status ahdunyi-test-api
```

#### 1.8 检查服务日志
```bash
# 查看服务日志
sudo journalctl -u ahdunyi-test-api -f

# 如果有错误，查看详细日志
sudo journalctl -u ahdunyi-test-api --no-pager -n 50
```

### 第二步：配置GitHub Actions自动部署（可选）

#### 2.1 在GitHub仓库设置Secrets
在GitHub仓库的 Settings → Secrets and variables → Actions 中添加：
- `TENCENT_CLOUD_HOST`: 腾讯云服务器IP地址
- `TENCENT_CLOUD_USER`: SSH用户名（如root）
- `TENCENT_CLOUD_SSH_KEY`: SSH私钥

#### 2.2 更新.env.test文件
更新项目根目录的`.env.test`文件：
- 设置正确的数据库连接信息
- 确认服务器地址和端口

#### 2.3 推送代码触发部署
```bash
git add .
git commit -m "feat: add test environment deployment"
git push origin develop
```

### 第三步：验证连接

#### 3.1 测试API连接
```bash
# 从本地测试
curl http://122.51.72.36:8002/health

# 应该返回：{"status":"ok","version":"9.1.0"}
```

#### 3.2 测试数据库连接
在腾讯云服务器上测试：
```bash
cd /app/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
python -c "
from server.core.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

#### 3.3 测试客户端连接
1. 使用当前`config.json`（已正确配置）
2. 打包EXE文件：
   ```bash
   python client/build/build.py
   ```
3. 运行EXE测试登录功能

### 第四步：常见问题排查

#### 4.1 如果仍然连接不上服务器
```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 8002/tcp

# 检查SELinux（如果启用）
getenforce
sudo setenforce 0  # 临时禁用，测试用

# 检查服务是否在监听
sudo lsof -i :8002
```

#### 4.2 如果数据库连接失败
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 检查MySQL用户权限
mysql -u ahdunyi_superyu -p -e "SHOW GRANTS;"

# 检查数据库是否存在
mysql -u ahdunyi_superyu -p -e "SHOW DATABASES;"
```

#### 4.3 如果服务启动失败
```bash
# 查看详细错误
cd /app/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
python -m server.main  # 直接运行查看错误

# 检查依赖
pip list | grep -E "fastapi|sqlalchemy|uvicorn"
```

## 紧急修复方案

如果急需测试环境可用，可以使用简化部署：

### 方案A：直接运行（不通过systemd）
```bash
cd /app/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
ENVIRONMENT=test uvicorn server.main:app --host 0.0.0.0 --port 8002 --reload
```

### 方案B：使用screen保持服务运行
```bash
screen -S ahdunyi-test
cd /app/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
ENVIRONMENT=test uvicorn server.main:app --host 0.0.0.0 --port 8002
# 按Ctrl+A，然后按D退出screen，服务继续运行
```

## 验证成功标准

1. ✅ `http://122.51.72.36:8002/health` 返回成功
2. ✅ `http://122.51.72.36:8002/docs` 可以访问API文档
3. ✅ 客户端EXE可以成功登录
4. ✅ 数据库操作正常（创建用户、查询任务等）

## 后续优化建议

1. **完善测试环境CI/CD**：使用创建好的`test-deploy.yml`
2. **环境分离**：为测试环境创建独立的数据库`ahdunyi_test_db`
3. **监控告警**：设置服务健康检查
4. **备份策略**：定期备份测试环境数据
5. **文档更新**：更新README中的测试环境部署说明