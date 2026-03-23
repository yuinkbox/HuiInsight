# GitHub Actions Secrets 配置指南

## 🔐 必需的环境变量和密钥

### 生产部署密钥 (server-deploy.yml)
这些密钥用于部署到阿里云生产服务器：

| 密钥名称 | 描述 | 示例值 |
|----------|------|--------|
| `ALIYUN_HOST` | 阿里云服务器IP地址或域名 | `106.15.32.246` |
| `ALIYUN_USER` | SSH登录用户名 | `root` 或 `ubuntu` |
| `ALIYUN_SSH_KEY` | SSH私钥（完整内容） | `-----BEGIN RSA PRIVATE KEY-----...` |

### 生产环境变量 (client-build.yml)
这些变量用于构建生产环境的前端应用：

| 密钥名称 | 描述 | 示例值 |
|----------|------|--------|
| `PRODUCTION_API_URL` | 生产环境API基础地址 | `http://106.15.32.246:8000` |

## ⚙️ 在GitHub仓库中配置Secrets

1. 访问仓库的 **Settings** 页面
2. 在左侧菜单中选择 **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 按钮
4. 输入密钥名称和值
5. 点击 **Add secret** 保存

## 🔒 安全最佳实践

1. **最小权限原则**：
   - 使用专用部署用户而非root
   - 限制SSH密钥的访问权限

2. **密钥轮换**：
   - 定期更新SSH密钥
   - 使用密钥对而非密码

3. **环境分离**：
   - 不同环境使用不同的密钥
   - 开发环境不使用生产密钥

## 🚨 紧急情况处理

如果密钥泄露：
1. 立即在阿里云控制台撤销泄露的SSH密钥
2. 在GitHub仓库中删除泄露的secret
3. 生成新的SSH密钥对
4. 更新所有相关配置

## 📋 验证配置

部署前验证：
```bash
# 验证SSH连接
ssh -i private_key.pem user@server_ip "echo 'SSH connection successful'"

# 验证服务状态
ssh -i private_key.pem user@server_ip "systemctl status ahdunyi-api"
```

## 🔧 故障排除

### 常见问题：
1. **SSH连接失败**：检查密钥格式和权限
2. **部署失败**：检查服务器磁盘空间和权限
3. **服务启动失败**：检查日志 `/var/log/ahdunyi-api.log`

### 日志位置：
- GitHub Actions日志：仓库的 **Actions** 标签页
- 服务器日志：`journalctl -u ahdunyi-api -f`