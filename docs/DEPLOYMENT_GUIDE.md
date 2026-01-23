# 部署指南 | Deployment Guide

本文档提供 Contract OS Simple 项目的完整部署方案，包括 Docker 部署、云平台部署和生产环境配置。

This document provides comprehensive deployment strategies for Contract OS Simple, including Docker deployment, cloud platform deployment, and production environment configuration.

## 目录 | Table of Contents

- [部署概述](#部署概述)
- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [云平台部署](#云平台部署)
- [生产环境配置](#生产环境配置)
- [监控与日志](#监控与日志)
- [备份与恢复](#备份与恢复)

## 部署概述

### 系统要求

#### 最低配置

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 存储 | 20 GB | 50 GB+ |
| Python | 3.11+ | 3.11+ |
| 操作系统 | Linux/macOS/Windows | Linux (Ubuntu 22.04) |

### 部署架构

```
┌─────────────────────────────────────────┐
│            Load Balancer (Optional)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Nginx / Reverse Proxy           │
│         (Port 80/443)                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     FastAPI Application (Port 8000)     │
│     - uvicorn workers                   │
│     - async task processing             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Data Layer                         │
│      - SQLite Database                  │
│      - Faiss Indexes                    │
│      - File Storage                     │
└─────────────────────────────────────────┘
```

## 本地部署

### 快速部署（开发环境）

#### 1. 环境准备

```bash
# 安装 Python 3.11+
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# macOS (使用 Homebrew)
brew install python@3.11

# 验证安装
python --version
```

#### 2. 项目部署

```bash
# 克隆代码
git clone <repository-url>
cd contract_os_simple

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r server/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 初始化数据库
python scripts/init_db.py

# 启动服务
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

#### 3. 使用 systemd 管理（Linux）

创建服务文件 `/etc/systemd/system/contract-os.service`:

```ini
[Unit]
Description=Contract OS Simple
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/contract_os_simple
Environment="PATH=/path/to/contract_os_simple/.venv/bin"
ExecStart=/path/to/contract_os_simple/.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable contract-os
sudo systemctl start contract-os
sudo systemctl status contract-os
```

### 使用 Supervisor

安装 Supervisor：

```bash
sudo apt install supervisor
```

配置文件 `/etc/supervisor/conf.d/contract-os.conf`:

```ini
[program:contract-os]
command=/path/to/.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/path/to/contract_os_simple
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/contract-os.log
```

管理命令：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start contract-os
sudo supervisorctl status contract-os
```

## Docker 部署

### 单容器部署

#### 1. 构建镜像

```bash
docker build -t contract-os-simple:latest .
```

#### 2. 运行容器

```bash
docker run -d \
  --name contract-os \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/storage:/app/storage \
  --env-file .env \
  contract-os-simple:latest
```

### Docker Compose 部署（推荐）

#### 1. 配置 docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: contract-os-app
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./storage:/app/storage
    environment:
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - DATABASE_PATH=/app/data/database.db
      - STORAGE_ROOT=/app/storage
      - MAX_CONCURRENT_TASKS=3
      - MAX_API_CONCURRENT=5
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 可选：添加 Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: contract-os-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
```

#### 2. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 查看状态
docker-compose ps

# 停止服务
docker-compose down

# 重启服务
docker-compose restart app
```

#### 3. 多实例部署（负载均衡）

```yaml
version: '3.8'

services:
  app:
    build: .
    deploy:
      replicas: 3  # 运行 3 个实例
      resources:
        limits:
          cpus: '1'
          memory: 2G
    environment:
      - DATABASE_PATH=/app/data/database.db
      # 共享存储（注意 SQLite 写锁问题）
    volumes:
      - ./data:/app/data
      - ./storage:/app/storage

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
```

Nginx 负载均衡配置 (`nginx-lb.conf`):

```nginx
events {
    worker_connections 1024;
}

http {
    upstream contract_os_backend {
        least_conn;
        server app:1:8000;
        server app:2:8000;
        server app:3:8000;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://contract_os_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Docker 最佳实践

#### 1. 镜像优化

```dockerfile
# 使用多阶段构建
FROM python:3.11-slim as builder

WORKDIR /app
COPY server/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY server/ .

# 非 root 用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
```

#### 3. 资源限制

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 云平台部署

### 部署到 AWS

#### 1. 使用 EC2

```bash
# 启动 EC2 实例（Ubuntu 22.04）
# 安全组开放端口：22, 80, 443, 8000

# SSH 连接
ssh -i your-key.pem ubuntu@ec2-xxx.amazonaws.com

# 安装 Docker
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu

# 克隆代码
git clone <repository-url>
cd contract_os_simple

# 配置环境变量
cp .env.example .env
nano .env

# 启动服务
docker-compose up -d
```

#### 2. 使用 AWS ECS

创建 `ecs-params.yml`:

```yaml
version: 1
task_definition:
  services:
    app:
      cpu_shares: 512
      mem_limit: 2048000000
      essential: true
```

部署：

```bash
# 配置 AWS CLI
aws configure

# 创建 ECS 集群
aws ecs create-cluster --cluster-name contract-os

# 部署服务
ecs-cli compose --ecs-params ecs-params.yml \
  --cluster contract-os up
```

#### 3. 使用 AWS RDS（可选，替换 SQLite）

如果需要使用 PostgreSQL 替代 SQLite：

```python
# .env
DATABASE_URL=postgresql+asyncpg://user:password@endpoint:5432/contract_os
```

### 部署到阿里云/腾讯云

#### 1. 使用云服务器 ECS/CVM

```bash
# 类似 EC2，使用 SSH 连接
ssh root@your-server-ip

# 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker root

# 部署应用
git clone <repository-url>
cd contract_os_simple
docker-compose up -d
```

#### 2. 使用容器服务

- 阿里云: ACK (Alibaba Cloud Container Service for Kubernetes)
- 腾讯云: TKE (Tencent Kubernetes Engine)

创建 Kubernetes 部署文件 `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-os
spec:
  replicas: 2
  selector:
    matchLabels:
      app: contract-os
  template:
    metadata:
      labels:
        app: contract-os
    spec:
      containers:
      - name: app
        image: your-registry/contract-os:latest
        ports:
        - containerPort: 8000
        env:
        - name: ZHIPU_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: zhipu-api-key
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: storage
          mountPath: /app/storage
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: contract-os-data
      - name: storage
        persistentVolumeClaim:
          claimName: contract-os-storage
---
apiVersion: v1
kind: Service
metadata:
  name: contract-os-service
spec:
  selector:
    app: contract-os
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

部署到 Kubernetes：

```bash
# 创建命名空间
kubectl create namespace contract-os

# 创建密钥
kubectl create secret generic api-keys \
  --from-literal=zhipu-api-key=your-key \
  -n contract-os

# 部署
kubectl apply -f k8s-deployment.yaml -n contract-os

# 查看状态
kubectl get pods -n contract-os
kubectl get services -n contract-os
```

### 部署到 Heroku

创建 `Procfile`:

```
web: uvicorn server.main:app --host 0.0.0.0 --port $PORT
```

部署：

```bash
# 登录 Heroku
heroku login

# 创建应用
heroku create your-app-name

# 设置环境变量
heroku config:set ZHIPU_API_KEY=your-key

# 部署
git push heroku main
```

## 生产环境配置

### Nginx 反向代理

配置文件 `/etc/nginx/sites-available/contract-os`:

```nginx
upstream contract_os_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/contract-os-access.log;
    error_log /var/log/nginx/contract-os-error.log;

    # 文件上传大小限制
    client_max_body_size 100M;

    location / {
        proxy_pass http://contract_os_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    # 静态文件缓存
    location /static {
        alias /path/to/storage;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/contract-os /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL 证书（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 环境变量配置

生产环境 `.env` 文件：

```bash
# 智谱AI配置
ZHIPU_API_KEY=your-production-key
ZHIPU_CHAT_MODEL=glm-4-flash
ZHIPU_EMBED_MODEL=embedding-3
ZHIPU_RERANK_MODEL=rerank-2

# 数据库
DATABASE_PATH=/app/data/database.db

# 存储
STORAGE_ROOT=/app/storage

# 服务器
HOST=0.0.0.0
PORT=8000
WORKERS=4  # 多 worker 进程

# CORS
CORS_ORIGINS=["https://your-domain.com"]

# 日志
LOG_LEVEL=INFO
LOG_FILE=/var/log/contract-os/app.log

# 并发
MAX_CONCURRENT_TASKS=5
MAX_API_CONCURRENT=10

# 安全
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=["your-domain.com"]
```

### 使用 Gunicorn（多 worker）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn server.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/contract-os/access.log \
  --error-logfile /var/log/contract-os/error.log \
  --log-level info
```

## 监控与日志

### 应用日志

```python
# server/config.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('/var/log/contract-os/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### 性能监控

#### 使用 Prometheus

```python
# server/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# 添加自定义指标
from prometheus_client import Counter

task_counter = Counter('tasks_total', 'Total tasks processed')
```

#### 查询指标：

```bash
curl http://localhost:8000/metrics
```

### 健康检查

```python
# server/routes/health.py
from fastapi import APIRouter
from server.database.connection import engine

router = APIRouter()

@router.get("/api/health")
async def health_check():
    # 检查数据库连接
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }
```

## 备份与恢复

### 数据库备份

```bash
# 创建备份脚本 backup.sh
#!/bin/bash
BACKUP_DIR="/backup/contract-os"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp /app/data/database.db $BACKUP_DIR/database_$DATE.db

# 备份 Faiss 索引
tar -czf $BACKUP_DIR/faiss_indexes_$DATE.tar.gz /app/data/faiss_indexes/

# 备份存储文件
tar -czf $BACKUP_DIR/storage_$DATE.tar.gz /app/storage/

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

定时任务：

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

### 数据库恢复

```bash
# 停止服务
docker-compose down

# 恢复数据库
cp /backup/contract-os/database_20240101_020000.db /app/data/database.db

# 恢复 Faiss 索引
tar -xzf /backup/contract-os/faiss_indexes_20240101_020000.tar.gz -C /

# 恢复存储
tar -xzf /backup/contract-os/storage_20240101_020000.tar.gz -C /

# 启动服务
docker-compose up -d
```

### 云存储备份（AWS S3）

```bash
# 安装 AWS CLI
pip install awscli

# 配置
aws configure

# 同步到 S3
aws s3 sync /app/data s3://your-bucket/contract-os-data/

# 定时同步
crontab -e
# 每小时同步
0 * * * * aws s3 sync /app/data s3://your-bucket/contract-os-data/
```

## 安全建议

1. **环境变量管理**
   - 使用密钥管理服务（AWS Secrets Manager、Azure Key Vault）
   - 不要在代码中硬编码密钥
   - 定期轮换 API 密钥

2. **网络安全**
   - 使用 HTTPS
   - 配置防火墙规则
   - 限制数据库访问

3. **应用安全**
   - 定期更新依赖
   - 启用 CORS 保护
   - 实施速率限制

4. **日志安全**
   - 不记录敏感信息
   - 定期审计日志
   - 设置日志保留策略

## 相关文档

- [开发指南](DEVELOPMENT_GUIDE.md)
- [API 文档](API_DOCUMENTATION.md)
- [故障排除](TROUBLESHOOTING.md)
