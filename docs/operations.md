# FuYellowBlueRed 运维文档

> 版本: v1.0
> 日期: 2026-05-20

---

## 目录

1. [环境要求](#1-环境要求)
2. [本地开发部署](#2-本地开发部署)
3. [Docker Compose 部署](#3-docker-compose-部署)
4. [生产环境部署](#4-生产环境部署)
5. [环境变量配置](#5-环境变量配置)
6. [数据库迁移](#6-数据库迁移)
7. [日志管理](#7-日志管理)
8. [监控与告警](#8-监控与告警)
9. [备份与恢复](#9-备份与恢复)
10. [常见问题](#10-常见问题)

---

## 1. 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 后端运行环境 |
| Node.js | 18+ | 前端构建环境 |
| MySQL | 8.0+ | 生产数据库 |
| Redis | 7.0+ | 缓存和延迟队列 |
| Docker | 20.10+ | 容器化部署 |
| Docker Compose | 2.0+ | 编排工具 |

---

## 2. 本地开发部署

### 2.1 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接等

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2.2 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 设置环境变量
cp .env.example .env
# 编辑 .env 配置后端 API 地址

# 启动开发服务器
npm run dev
```

### 2.3 访问地址

- 后端 API: http://localhost:8000
- 前端页面: http://localhost:5173
- API 文档: http://localhost:8000/docs
- Prometheus 指标: http://localhost:8000/metrics

---

## 3. Docker Compose 部署

### 3.1 启动全部服务

```bash
# 从项目根目录启动
docker-compose up -d
```

### 3.2 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8000 | 后端 API |
| frontend | 80 | 前端应用 |
| redis | 6379 | 缓存服务 |
| mysql | 3306 | 数据库（可选）|

### 3.3 常用命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart backend

# 停止服务
docker-compose down

# 查看服务状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
```

---

## 4. 生产环境部署

### 4.1 环境准备

```bash
# 创建目录结构
mkdir -p /opt/fuyellowbluered/{backend,frontend,logs,uploads}

# 设置权限
chown -R www-data:www-data /opt/fuyellowbluered
```

### 4.2 后端配置

```bash
# 创建生产配置文件
cat > /opt/fuyellowbluered/backend/.env << EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/fuyellowbluered
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://your-domain.com
EOF
```

### 4.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/fuyellowbluered/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4.4 系统服务配置

```bash
cat > /etc/systemd/system/fuyellowbluered-backend.service << EOF
[Unit]
Description=FuYellowBlueRed Backend Service
After=network.target redis.target mysql.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fuyellowbluered/backend
Environment="PATH=/opt/fuyellowbluered/backend/venv/bin"
ExecStart=/opt/fuyellowbluered/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable fuyellowbluered-backend
systemctl start fuyellowbluered-backend
```

---

## 5. 环境变量配置

### 5.1 后端环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| ENVIRONMENT | 运行环境 | development | 否 |
| DEBUG | 调试模式 | true | 否 |
| DATABASE_URL | 数据库连接URL | sqlite+aiosqlite:///./data.db | 是 |
| REDIS_URL | Redis连接URL | redis://localhost:6379/0 | 否 |
| JWT_SECRET_KEY | JWT密钥 | - | 是 |
| JWT_ALGORITHM | JWT算法 | HS256 | 否 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | Access Token有效期(分钟) | 15 | 否 |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | Refresh Token有效期(天) | 7 | 否 |
| CORS_ORIGINS | CORS允许的域名 | http://localhost:5173 | 是 |
| UPLOAD_DIR | 文件上传目录 | uploads | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| MAX_UPLOAD_SIZE | 最大上传文件大小(MB) | 5 | 否 |

### 5.2 前端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_API_URL | 后端API地址 | http://localhost:8000 |
| VITE_APP_NAME | 应用名称 | FuYellowBlueRed |

---

## 6. 数据库迁移

### 6.1 创建迁移

```bash
# 创建新的迁移脚本
alembic revision --autogenerate -m "description of changes"

# 查看迁移历史
alembic history

# 执行迁移
alembic upgrade head

# 回滚到上一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

### 6.2 迁移脚本规范

1. 每次迁移必须包含 `upgrade()` 和 `downgrade()` 方法
2. 迁移脚本应保持幂等性
3. 大表迁移应分批执行，避免锁表
4. 生产环境迁移前应备份数据库

---

## 7. 日志管理

### 7.1 日志配置

后端日志默认输出到控制台和文件，日志级别可通过 `LOG_LEVEL` 环境变量配置。

### 7.2 日志轮转

```bash
cat > /etc/logrotate.d/fuyellowbluered << EOF
/opt/fuyellowbluered/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
EOF
```

### 7.3 日志位置

| 服务 | 日志路径 |
|------|----------|
| 后端 | `/opt/fuyellowbluered/logs/backend.log` |
| Nginx | `/var/log/nginx/access.log` |
| MySQL | `/var/log/mysql/error.log` |

---

## 8. 监控与告警

### 8.1 Prometheus 配置

```yaml
scrape_configs:
  - job_name: 'fuyellowbluered-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 8.2 关键指标

| 指标名 | 说明 |
|--------|------|
| `http_requests_total` | 请求总数 |
| `http_request_duration_seconds` | 请求耗时 |
| `active_websocket_connections` | WebSocket连接数 |
| `redis_connected_clients` | Redis连接数 |

### 8.3 告警规则

```yaml
groups:
  - name: fuyellowbluered
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High request latency detected"
```

---

## 9. 备份与恢复

### 9.1 数据库备份

```bash
# MySQL 备份
mysqldump -u root -p fuyellowbluered > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite 备份
cp /path/to/data.db backup_$(date +%Y%m%d_%H%M%S).db
```

### 9.2 数据库恢复

```bash
# MySQL 恢复
mysql -u root -p fuyellowbluered < backup_20260520_120000.sql

# SQLite 恢复
cp backup_20260520_120000.db /path/to/data.db
```

### 9.3 备份策略

| 类型 | 频率 | 保留时间 |
|------|------|----------|
| 每日备份 | 每天凌晨 2:00 | 7天 |
| 每周备份 | 每周日凌晨 2:00 | 4周 |
| 每月备份 | 每月1日凌晨 2:00 | 12个月 |

---

## 10. 常见问题

### 10.1 服务无法启动

**问题**: 后端服务启动失败

**排查步骤**:
1. 检查环境变量配置是否正确
2. 检查数据库连接是否正常
3. 检查端口是否被占用
4. 查看日志文件获取详细错误信息

```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 查看服务日志
journalctl -u fuyellowbluered-backend -f
```

### 10.2 数据库连接失败

**问题**: 后端无法连接数据库

**排查步骤**:
1. 检查数据库服务是否运行
2. 检查数据库连接URL配置
3. 检查数据库用户权限
4. 检查防火墙规则

```bash
# 检查 MySQL 服务
systemctl status mysql

# 测试数据库连接
mysql -h localhost -u username -p
```

### 10.3 Redis 连接失败

**问题**: 缓存功能无法使用

**排查步骤**:
1. 检查 Redis 服务是否运行
2. 检查 Redis 连接配置
3. 检查 Redis 密码配置

```bash
# 检查 Redis 服务
systemctl status redis

# 测试 Redis 连接
redis-cli ping
```

### 10.4 文件上传失败

**问题**: 上传文件时报错

**排查步骤**:
1. 检查上传目录权限
2. 检查文件大小是否超限
3. 检查文件类型是否在白名单中

```bash
# 检查上传目录权限
ls -la /opt/fuyellowbluered/uploads
```

---

## 附录：故障排查清单

| 问题现象 | 可能原因 | 排查方向 |
|----------|----------|----------|
| 500 错误 | 代码异常 | 查看后端日志 |
| 401 错误 | Token 无效 | 检查 JWT 密钥配置 |
| 403 错误 | 权限不足 | 检查用户角色 |
| 连接超时 | 服务未启动 | 检查服务状态 |
| 响应缓慢 | 数据库慢查询 | 优化 SQL 查询 |

---

*文档版本: v1.0*
*最后更新: 2026-05-20*