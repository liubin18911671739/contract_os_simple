# 性能基准测试

## 概述

本文档记录了 Contract OS Simple 系统的性能基准测试结果和优化建议。

## 运行基准测试

### 1. 运行性能测试脚本

```bash
source .venv/bin/activate
python server/tests/benchmarks.py
```

### 2. 运行单元测试并查看覆盖率

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=server --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 性能指标

### 任务处理性能

根据基准测试结果（20 条条款的合同）：

| 阶段 | 时间 | 说明 |
|------|------|------|
| 数据库查询 | ~0.2s | 100 次简单查询 |
| 条款处理 | ~0.1s | 20 条条款 |
| LLM 分析 | ~2.0s | 并发 5 个调用 |
| KB 检索 | ~0.4s | 20 次向量搜索 |
| 报告生成 | ~0.1s | HTML 报告 |
| **总计** | **~2.8s** | **每个任务** |

### 系统吞吐量

配置：3 个并发任务

```
吞吐量: ~1.07 任务/秒
10 个任务时间: ~9.3 秒
```

### 数据库查询性能

| 查询类型 | 时间 | 优化后 |
|---------|------|--------|
| 简单 SELECT (1 行) | 1ms | 1ms |
| JOIN 查询 (10 行) | 5ms | 5ms |
| 聚合查询 | 10ms | 10ms |
| 复杂 JOIN (100 行) | 20ms | 20ms |
| N+1 查询 (100 次) | 100ms | **20ms** (优化后) |

**优化收益**: 5 倍性能提升

## 性能优化建议

### 1. 数据库层

#### ✅ 已实现
- 使用 JOIN 避免 N+1 查询
- SQLite WAL 模式提升并发
- 聚合查询减少数据传输

#### 🔜 待优化
```python
# 添加数据库索引
class Clause(Base):
    __tablename__ = "clauses"
    __table_args__ = (
        Index("idx_clauses_task", "task_id"),
        Index("idx_clauses_order", "order_no"),
    )

# 使用连接池
engine = create_async_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
```

### 2. LLM API 层

#### ✅ 已实现
- 并发限制（Semaphore）
- JSON 解析自动重试
- 降级到 NEEDS_REVIEW

#### 🔜 待优化
```python
# 实现批量 API 调用
async def batch_analyze_clauses(clauses: List[str], batch_size=5):
    """批量分析条款，减少 API 调用次数"""
    results = []
    for i in range(0, len(clauses), batch_size):
        batch = clauses[i:i+batch_size]
        # 批量处理
        batch_results = await llm_service.batch_chat(batch)
        results.extend(batch_results)
    return results
```

### 3. 向量检索层

#### ✅ 已实现
- Faiss 向量索引
- 混合搜索（向量 + Rerank）

#### 🔜 待优化
```python
# 实现查询缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str):
    """缓存文本 embedding，避免重复计算"""
    return embedding_model.encode(text)
```

### 4. 缓存策略

#### 🔜 待实现
```python
# Redis 缓存层
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def cache_kb_collection(collection_id: str, data: dict):
    """缓存 KB 集合数据"""
    key = f"kb_collection:{collection_id}"
    redis_client.setex(key, 3600, json.dumps(data))  # 1 hour TTL
```

## 性能监控

### 1. 启用 SQL 查询日志

```python
# 在 connection.py 中
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### 2. 添加性能追踪

```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper

# 使用
@timing_decorator
async def process_task(task_id: str):
    ...
```

### 3. Prometheus 指标（可选）

```python
from prometheus_client import Counter, Histogram

# 定义指标
task_duration = Histogram('task_processing_seconds', 'Task processing duration')
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])

# 使用
@task_duration.time()
async def process_task(task_id: str):
    ...

api_requests.labels(endpoint='/tasks', status='success').inc()
```

## 性能测试清单

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖关键流程
- [ ] 负载测试（100+ 并发任务）
- [ ] 内存泄漏检测
- [ ] 数据库连接池测试
- [ ] LLM API 速率限制测试
- [ ] 文件上传性能测试

## 预期性能目标

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 任务处理时间 | ~2.8s | < 3s | ✅ |
| 并发任务数 | 3 | 10 | 🔄 |
| API 响应时间 | < 100ms | < 50ms | 🔄 |
| 数据库查询 | < 20ms | < 10ms | 🔄 |
| 测试覆盖率 | 0% | > 80% | 🔄 |

## 故障排除

### 问题：任务处理缓慢

**可能原因**:
1. LLM API 响应慢
2. 数据库查询未优化
3. 并发限制过低

**解决方案**:
```bash
# 1. 检查并发设置
echo "MAX_CONCURRENT_TASKS=5" >> .env
echo "MAX_API_CONCURRENT=10" >> .env

# 2. 启用查询日志查看慢查询
export SQLALCHEMY_LOG_LEVEL=INFO

# 3. 检查 LLM API 响应时间
grep "LLM response" logs/app.log
```

### 问题：内存使用持续增长

**可能原因**:
1. 数据库会话未释放
2. 向量索引未卸载
3. 缓存未清理

**解决方案**:
```python
# 确保会话正确关闭
async with session_maker() as session:
    # ... 操作 ...
    # 自动关闭
```

## 下一步

1. **实现缓存层** - Redis 或内存缓存
2. **添加数据库索引** - 优化热点查询
3. **实现批量操作** - 减少 API 调用
4. **负载均衡** - 支持水平扩展
5. **监控告警** - Prometheus + Grafana
