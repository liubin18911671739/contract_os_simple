# 故障排除指南 | Troubleshooting Guide

本文档提供 Contract OS Simple 项目的常见问题诊断和解决方案。

This document provides common issue diagnosis and solutions for Contract OS Simple.

## 目录 | Table of Contents

- [快速诊断](#快速诊断)
- [环境问题](#环境问题)
- [数据库问题](#数据库问题)
- [LLM API 问题](#llm-api-问题)
- [文件处理问题](#文件处理问题)
- [性能问题](#性能问题)
- [部署问题](#部署问题)
- [调试技巧](#调试技巧)

## 快速诊断

### 服务健康检查

```bash
# 1. 检查服务是否运行
curl http://localhost:8000/api/health

# 2. 检查端口是否被占用
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 3. 检查进程
ps aux | grep uvicorn  # macOS/Linux
tasklist | findstr python  # Windows

# 4. 查看日志
tail -f /var/log/contract-os/app.log
```

### 常见错误速查

| 错误信息 | 可能原因 | 快速解决 |
|---------|---------|---------|
| `ModuleNotFoundError` | 依赖未安装 | `pip install -r server/requirements.txt` |
| `sqlite3.OperationalError: database is locked` | 数据库锁定 | 检查 WAL 模式，关闭长时间事务 |
| `APIError: 401` | API 密钥错误 | 检查 `.env` 中的 `ZHIPU_API_KEY` |
| `TypeError: 'NoneType' object is not iterable` | 数据未正确初始化 | 运行 `python scripts/init_db.py` |
| `Connection refused` | 服务未启动 | 检查 uvicorn 进程 |

## 环境问题

### Python 版本不兼容

**症状**:
```
SyntaxError: str | None is not valid
```

**原因**: Python 版本低于 3.11

**解决方案**:
```bash
# 检查 Python 版本
python --version

# 使用 pyenv 安装 3.11
brew install pyenv  # macOS
pyenv install 3.11.7
pyenv local 3.11.7

# 或使用 conda
conda create -n contract_os python=3.11
conda activate contract_os
```

### 虚拟环境问题

**症状**:
```
Command not found: uvicorn
```

**解决方案**:
```bash
# 确认虚拟环境已激活
which python  # 应指向 .venv/bin/python

# 重新创建虚拟环境
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt
```

### 依赖冲突

**症状**:
```
ERROR: pip's dependency resolver does not currently take into account...
```

**解决方案**:
```bash
# 清理并重新安装
pip install pip-upgrade
pip install --upgrade pip
pip install -r server/requirements.txt --force-reinstall

# 或使用 pip-tools
pip install pip-tools
pip-compile server/requirements.txt
pip-sync
```

### 环境变量未加载

**症状**:
```
KeyError: 'ZHIPU_API_KEY'
```

**解决方案**:
```bash
# 1. 确认 .env 文件存在
ls -la .env

# 2. 检查 .env 格式（无空格）
cat .env | grep ZHIPU_API_KEY

# 3. 确保在应用启动前加载
# 在代码中：
from dotenv import load_dotenv
load_dotenv()

# 4. 手动导出（临时）
export ZHIPU_API_KEY="your-key"
```

## 数据库问题

### 数据库锁定

**症状**:
```
sqlite3.OperationalError: database is locked
```

**诊断**:
```bash
# 检查 WAL 模式
sqlite3 data/database.db "PRAGMA journal_mode;"

# 查看锁定进程
lsof data/database.db
```

**解决方案**:

1. **启用 WAL 模式**:
```bash
sqlite3 data/database.db "PRAGMA journal_mode=WAL;"
```

2. **检查长事务**:
```python
# 确保所有数据库操作都使用 context manager
async with session_maker() as session:
    # 操作
    pass  # 自动提交/回滚
```

3. **降低并发**:
```bash
# .env
MAX_CONCURRENT_TASKS=1
```

### 数据库文件损坏

**症状**:
```
sqlite3.DatabaseError: database disk image is malformed
```

**解决方案**:
```bash
# 1. 尝试修复
sqlite3 data/database.db "PRAGMA integrity_check;"
sqlite3 data/database.db "VACUUM;"

# 2. 导出数据
sqlite3 data/database.db ".dump" > backup.sql

# 3. 重建数据库
rm data/database.db
python scripts/init_db.py
sqlite3 data/database.db < backup.sql
```

### 表不存在

**症状**:
```
sqlite3.OperationalError: no such table: precheck_tasks
```

**解决方案**:
```bash
# 初始化数据库
python scripts/init_db.py

# 验证表已创建
sqlite3 data/database.db ".tables"
```

### 迁移问题

**症状**:
```
Column 'new_column' does not exist
```

**解决方案**:
```bash
# 当前版本使用简单初始化脚本
# 重置数据库（注意：会丢失数据）
rm data/database.db
python scripts/init_db.py

# 或手动添加列
sqlite3 data/database.db "ALTER TABLE precheck_tasks ADD COLUMN new_column TEXT;"
```

## LLM API 问题

### API 密钥无效

**症状**:
```
zhipuai.core._errors.APIError: 401 - Invalid API key
```

**解决方案**:
```bash
# 1. 检查 API 密钥
echo $ZHIPU_API_KEY

# 2. 更新 .env 文件
nano .env
# ZHIPU_API_KEY=your-correct-key

# 3. 测试密钥
curl -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4-flash","messages":[{"role":"user","content":"test"}]}'
```

### API 限流

**症状**:
```
zhipuai.core._errors.APIError: 429 - Rate limit exceeded
```

**解决方案**:
```bash
# 1. 降低并发
# .env
MAX_API_CONCURRENT=2

# 2. 添加重试逻辑
# 已在 llm_service.py 中实现自动重试

# 3. 使用指数退避
# 在代码中已实现
```

### API 超时

**症状**:
```
TimeoutError: Request timeout
```

**解决方案**:
```python
# server/services/llm_service.py
# 增加超时时间
client = ZhipuAI(
    api_key=settings.zhipu_api_key,
    timeout=60.0  # 增加到 60 秒
)
```

### JSON 解析失败

**症状**:
```
JSONDecodeError: Expecting value
```

**原因**: LLM 返回的 JSON 格式不正确

**解决方案**:
```python
# 已在 llm_service.py 中实现自动修复
# chat_with_json() 方法会：
# 1. 尝试直接解析
# 2. 失败后请求 LLM 修复
# 3. 再次尝试解析
# 4. 最终失败返回 None
```

### 余额不足

**症状**:
```
zhipuai.core._errors.APIError: 402 - Insufficient balance
```

**解决方案**:
1. 登录 [智谱AI 平台](https://open.bigmodel.cn/) 充值
2. 检查余额：`https://open.bigmodel.cn/usercenter/balance`
3. 考虑切换到付费模型

## 文件处理问题

### PDF 解析失败

**症状**:
```
PyPDF2.errors.PdfReadError: PDF file is damaged
```

**解决方案**:
```python
# 尝试使用备用库
pip install pdfplumber

# 修改 file_parser.py
import pdfplumber

def parse_pdf_fallback(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)
```

### DOCX 解析失败

**症状**:
```
KeyError: "Invalid docx file"
```

**解决方案**:
```bash
# 确保 docx 文件未损坏
# 尝试用 Word 打开并另存为

# 或使用备用库
pip install python-docx-txt
```

### 文本编码错误

**症状**:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc8
```

**解决方案**:
```python
# 已在 file_parser.py 中实现自动检测编码
# parse_txt() 会尝试：UTF-8 → GBK → GB2312

# 手动指定编码
with open(file_path, 'r', encoding='gbk') as f:
    text = f.read()
```

### 文件大小限制

**症状**:
```
Request body size limit exceeded
```

**解决方案**:
```python
# server/main.py
app = FastAPI()

# 增加上传限制
@app.post("/api/contracts/{id}/versions")
async def upload_version(
    id: str,
    file: UploadFile = File(..., max_size=100 * 1024 * 1024)  # 100MB
):
    pass
```

### 存储空间不足

**症状**:
```
OSError: [Errno 28] No space left on device
```

**解决方案**:
```bash
# 1. 检查磁盘空间
df -h

# 2. 清理旧文件
find storage/ -name "*.tmp" -delete

# 3. 压缩日志
gzip /var/log/contract-os/*.log

# 4. 设置日志轮转
# /etc/logrotate.d/contract-os
/var/log/contract-os/*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

## 性能问题

### 任务处理缓慢

**症状**: 单个任务超过 10 分钟

**诊断**:
```python
# 添加性能监控
import time

async def execute(task_id: int, payload: dict) -> dict:
    start = time.time()
    # ... 处理逻辑
    duration = time.time() - start
    await log_event(task_id, "DEBUG", f"Stage took {duration:.2f}s")
```

**优化方案**:

1. **增加并发**:
```bash
# .env
MAX_CONCURRENT_TASKS=5
MAX_API_CONCURRENT=10
```

2. **优化 LLM 调用**:
```python
# 批量处理
texts = [...]  # 多个文本
embeddings = await llm_service.embed(texts, batch_size=10)
```

3. **缓存结果**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_kb_collection(collection_id: int):
    # 缓存 KB 集合
    pass
```

### 内存占用过高

**症状**: 进程内存超过 2GB

**诊断**:
```bash
# 检查内存使用
ps aux | grep uvicorn

# 使用 memory_profiler
pip install memory_profiler
python -m memory_profiler server/main.py
```

**解决方案**:

1. **清理缓存**:
```python
# 定期清理 Faiss 索引缓存
from server.utils.vector_store import clear_cache
async def cleanup_task():
    while True:
        await asyncio.sleep(3600)  # 每小时
        clear_cache()
```

2. **限制批量大小**:
```python
# 减少批量处理大小
embeddings = await llm_service.embed(texts, batch_size=5)
```

3. **使用生成器**:
```python
# 避免一次性加载所有数据
async def process_clauses_stream(task_id: int):
    async for clause in stream_clauses(task_id):
        yield await process_clause(clause)
```

### CPU 占用过高

**症状**: CPU 使用率持续 100%

**诊断**:
```bash
# 使用 Python profiler
python -m cProfile -o profile.out server/main.py
python -m pstats profile.out
```

**解决方案**:

1. **减少不必要的计算**:
```python
# 缓存计算结果
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_function(param: str):
    # 复杂计算
    return result
```

2. **使用异步 I/O**:
```python
# 避免阻塞调用
# 错误：
time.sleep(1)  # 阻塞

# 正确：
await asyncio.sleep(1)  # 非阻塞
```

## 部署问题

### Docker 容器无法启动

**症状**:
```
docker: Error response from daemon: ...
```

**诊断**:
```bash
# 查看容器日志
docker logs contract-os-app

# 检查容器状态
docker ps -a

# 进入容器检查
docker exec -it contract-os-app bash
```

**解决方案**:

1. **检查端口冲突**:
```bash
# 停止占用端口的容器
docker stop $(docker ps -q -f publish=8000)
```

2. **检查挂载路径**:
```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data  # 确保路径正确
```

3. **重建镜像**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据持久化失败

**症状**: 容器重启后数据丢失

**解决方案**:
```yaml
# docker-compose.yml
services:
  app:
    volumes:
      - ./data:/app/data:rw  # 确保读写权限
      - ./storage:/app/storage:rw

# 检查权限
ls -la data/
```

### 健康检查失败

**症状**:
```
Health check failed
```

**解决方案**:
```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"
```

### Nginx 反向代理错误

**症状**: 502 Bad Gateway

**诊断**:
```bash
# 检查 Nginx 日志
tail -f /var/log/nginx/error.log

# 检查后端服务
curl http://localhost:8000/api/health
```

**解决方案**:
```nginx
# nginx.conf
upstream contract_os_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    location / {
        proxy_pass http://contract_os_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

## 调试技巧

### 启用详细日志

```python
# server/config.py
import logging

logging.basicConfig(
    level=logging.DEBUG,  # 最详细
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/contract-os/debug.log'),
        logging.StreamHandler()
    ]
)
```

### 使用 Python 调试器

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更好的交互）
import ipdb; ipdb.set_trace()
```

### 数据库查询日志

```python
# 启用 SQLAlchemy 查询日志
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 性能分析

```bash
# 使用 cProfile
python -m cProfile -o profile.stats server/main.py

# 分析结果
python -m pstats profile.stats
> % cumtime  # 按累计时间排序
> top 10
```

### API 请求追踪

```python
# server/main.py
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url} - {response.status_code} - {duration:.2f}s")
    return response
```

## 日志位置

### 开发环境
- 应用日志：控制台输出
- 数据库：`data/database.db`
- Faiss 索引：`data/faiss_indexes/`
- 存储文件：`storage/`

### 生产环境
- 应用日志：`/var/log/contract-os/app.log`
- 错误日志：`/var/log/contract-os/error.log`
- Nginx 日志：`/var/log/nginx/`
- Docker 日志：`docker-compose logs -f app`

## 获取帮助

如果以上方法都无法解决问题：

1. **查看事件日志**:
```bash
sqlite3 data/database.db "SELECT * FROM task_events ORDER BY ts DESC LIMIT 20;"
```

2. **检查 GitHub Issues**:
   搜索类似问题的解决方案

3. **创建新的 Issue**:
   包含以下信息：
   - 错误信息
   - 环境信息（OS、Python 版本）
   - 相关日志
   - 复现步骤

## 相关文档

- [开发指南](DEVELOPMENT_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [API 文档](API_DOCUMENTATION.md)
