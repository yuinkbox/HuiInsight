# 腾讯云服务器测试环境部署指令

**收件人：** openclaw  
**主题：** 在腾讯云服务器（122.51.72.36）部署AHDUNYI测试环境  
**紧急程度：** 高  

---

## 📋 部署目标

在腾讯云服务器（122.51.72.36:8002）部署AHDUNYI Terminal PRO的测试环境，解决当前客户端连接不上的问题。

## 🔍 当前问题诊断

1. **服务器地址**：`http://122.51.72.36:8002`
2. **现状**：端口8002开放，但返回502错误（Bad Gateway）
3. **问题原因**：后端FastAPI服务未运行或配置错误
4. **影响**：客户端EXE无法登录测试环境

## 🚀 部署步骤

### 第一步：登录服务器并检查现状

```bash
ssh root@122.51.72.36

# 检查当前服务状态
systemctl list-units | grep ahdunyi

# 检查端口占用
netstat -tlnp | grep :8002

# 检查Nginx配置（如果有）
nginx -t 2>/dev/null && echo "Nginx installed" || echo "Nginx not found"
```

### 第二步：停止可能冲突的服务

```bash
# 如果有错误的服务，先停止
systemctl stop ahdunyi-api 2>/dev/null || true
systemctl stop ahdunyi-test-api 2>/dev/null || true

# 确认端口释放
lsof -i :8002
# 如果有进程占用，使用 kill -9 <PID> 结束
```

### 第三步：部署测试环境代码

```bash
# 进入应用目录
cd /app

# 如果已有项目，更新代码
if [ -d "AHDUNYI_Terminal_PRO" ]; then
    cd AHDUNYI_Terminal_PRO
    git fetch origin
    git checkout develop
    git pull origin develop
else
    # 首次部署，克隆代码
    git clone https://github.com/yuinkbox/AHDUNYI_Terminal_PRO.git
    cd AHDUNYI_Terminal_PRO
    git checkout develop
fi
```

### 第四步：配置测试环境

```bash
# 创建测试环境配置文件
cat > server/.env << 'EOF'
ENVIRONMENT=test
DATABASE_URL=mysql+pymysql://ahdunyi_superyu:[请填写测试数据库密码]@[请填写腾讯云MySQL IP]:3306/ahdunyi_test_db?charset=utf8mb4
JWT_SECRET_KEY=test-jwt-secret-key-change-for-security
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
SERVER_HOST=0.0.0.0
SERVER_PORT=8002
DEBUG=true
APP_NAME=AHDUNYI Terminal PRO (Test)
APP_VERSION=9.1.0
EOF

# 注意：需要填写以下信息：
# 1. [请填写测试数据库密码] - 测试数据库的密码
# 2. [请填写腾讯云MySQL IP] - 腾讯云MySQL服务器的IP地址
```

### 第五步：设置Python环境

```bash
cd server

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 创建Python虚拟环境"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -r requirements.txt
```

### 第六步：配置systemd服务

```bash
# 复制服务配置文件
sudo cp ahdunyi-test-api.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable ahdunyi-test-api

# 启动服务
sudo systemctl start ahdunyi-test-api
```

### 第七步：验证部署

```bash
# 检查服务状态
sudo systemctl status ahdunyi-test-api

# 查看服务日志
sudo journalctl -u ahdunyi-test-api --no-pager -n 20

# 测试API连接
curl http://localhost:8002/health
# 应该返回：{"status":"ok","version":"9.1.0"}

# 测试外部访问
curl http://122.51.72.36:8002/health
```

### 第八步：防火墙和安全组配置

```bash
# 检查防火墙
sudo ufw status

# 如果防火墙启用，开放8002端口
sudo ufw allow 8002/tcp

# 检查腾讯云安全组（需要在控制台操作）
# 确保安全组允许8002端口的入站流量
```

## 🛠️ 故障排除

### 如果服务启动失败：

```bash
# 查看详细错误日志
sudo journalctl -u ahdunyi-test-api -f

# 手动运行服务查看错误
cd /app/AHDUNYI_Terminal_PRO/server
source venv/bin/activate
ENVIRONMENT=test uvicorn server.main:app --host 0.0.0.0 --port 8002
```

### 如果数据库连接失败：

```bash
# 测试MySQL连接
mysql -u ahdunyi_superyu -p -h [MySQL IP] -e "SELECT 1;"

# 检查数据库是否存在
mysql -u ahdunyi_superyu -p -h [MySQL IP] -e "SHOW DATABASES;"
```

### 如果端口被占用：

```bash
# 查找占用8002端口的进程
lsof -i :8002

# 结束占用进程
kill -9 <PID>
```

## 📞 需要的信息

请openclaw提供以下信息：

1. **测试数据库密码**：用于连接腾讯云MySQL
2. **腾讯云MySQL IP地址**：测试数据库服务器的IP
3. **当前服务器状态**：执行第一步检查的结果
4. **遇到的任何错误**：部署过程中的错误信息

## ✅ 成功标准

部署完成后，请验证以下内容：

1. ✅ `sudo systemctl status ahdunyi-test-api` 显示服务运行正常
2. ✅ `curl http://122.51.72.36:8002/health` 返回 `{"status":"ok","version":"9.1.0"}`
3. ✅ `curl http://122.51.72.36:8002/docs` 可以访问API文档
4. ✅ 客户端EXE可以成功登录测试环境

## ⏱️ 时间要求

**紧急**：请尽快完成部署，当前测试环境不可用影响测试进度。

---

**联系人**：yuinkbox  
**问题反馈**：部署过程中遇到任何问题，请及时联系并提供错误日志。