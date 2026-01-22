# 数据库查询优化说明

## 概述

本文档记录了为避免 N+1 查询问题而实施的数据库查询优化。

## 什么是 N+1 查询问题？

N+1 查询问题是指：
- 1 次查询获取主对象列表（如获取所有 risks）
- N 次查询获取每个关联对象（如为每个 risk 单独查询对应的 clause）
- 总共执行 N+1 次查询，导致性能问题

## 已实施的优化

### 1. TaskService.get_task_clauses()

**文件**: `server/services/task_service.py:372-427`

**优化方式**: 使用 JOIN 一次性获取 clauses 和关联的 risks

```python
query = (
    select(
        Clause.id,
        Clause.clause_id,
        Clause.title,
        Clause.text,
        Clause.order_no,
        Risk.id.label("risk_id"),
        Risk.risk_level,
        Risk.summary,
        Risk.status,
    )
    .select_from(Clause)
    .outerjoin(Risk, and_(
        Risk.clause_id == Clause.clause_id,
        Risk.task_id == Clause.task_id
    ))
    .where(Clause.task_id == task_id)
)
```

**效果**:
- ❌ 优化前: 1 次查询 clauses + N 次查询 risks = N+1 次查询
- ✅ 优化后: 1 次查询获取所有数据

### 2. EvidenceAgent.execute()

**文件**: `server/agents/stub_agents.py:185-222`

**优化方式**: 使用 JOIN 一次性获取 risks 和关联的 clauses

```python
query = (
    select(Risk, Clause)
    .select_from(Risk)
    .join(Clause, Risk.clause_id == Clause.clause_id)
    .where(Risk.task_id == task_id)
)
result = await self.session.execute(query)
risk_clause_pairs = result.all()

for risk, clause in risk_clause_pairs:
    # 直接使用已加载的 clause，无需额外查询
    contract_evidence = Evidence(
        id=f"ev_{uuid.uuid4().hex[:12]}",
        risk_id=risk.id,
        source_type="CONTRACT",
        quote_text=clause.text[:500],
        page_ref=clause.page_ref,
    )
```

**效果**:
- ❌ 优化前: 1 次查询 risks + N 次查询 clauses = N+1 次查询
- ✅ 优化后: 1 次查询获取所有数据

### 3. ReportAgent._gather_report_data()

**文件**: `server/agents/report_agent.py`

**优化方式**: 使用聚合查询和 JOIN 一次性获取统计数据

```python
# 获取条款和风险的聚合统计
clauses_with_risks = await fetch_all_sql(
    """
    SELECT
        c.clause_id,
        c.order_no,
        c.text,
        c.type,
        c.page_ref,
        COUNT(r.id) as risk_count,
        COUNT(r.id) FILTER (WHERE r.risk_level = 'HIGH') as high_risk_count,
        ...
    FROM clauses c
    LEFT JOIN risks r ON r.clause_id = c.clause_id
    WHERE c.task_id = ?
    GROUP BY c.clause_id
    """,
    (task_id,),
)

# 获取风险详情及其关联数据
all_risks = await fetch_all_sql(
    """
    SELECT
        r.id,
        r.risk_level,
        ...
        COUNT(DISTINCT ev.id) as evidence_count,
        COUNT(DISTINCT kb.id) as kb_citation_count
    FROM risks r
    JOIN clauses c ON c.clause_id = r.clause_id
    LEFT JOIN evidences ev ON ev.risk_id = r.id
    LEFT JOIN kb_citations kb ON kb.risk_id = r.id
    WHERE r.task_id = ?
    GROUP BY r.id, c.order_no
    """,
    (task_id,),
)
```

**效果**:
- ❌ 优化前: 多次查询获取统计、风险、证据、引用数据
- ✅ 优化后: 2 次查询获取所有报告数据

### 4. TaskService.list_tasks()

**文件**: `server/services/task_service.py:152-232`

**优化方式**: 使用 JOIN 一次性获取 tasks 和关联的 contract 信息

```python
query = (
    select(
        PrecheckTask.id,
        PrecheckTask.status,
        ...
        Contract.contract_name,
    )
    .select_from(PrecheckTask)
    .join(ContractVersion, PrecheckTask.contract_version_id == ContractVersion.id)
    .join(Contract, ContractVersion.contract_id == Contract.id)
)
```

**效果**:
- ❌ 优化前: 1 次查询 tasks + N 次查询 contract = N+1 次查询
- ✅ 优化后: 1 次查询获取所有任务和合同信息

## 性能提升

假设一个典型的场景：
- 50 个 tasks
- 每个 task 有 20 个 risks
- 每个 risk 有 1 个 clause

**优化前**:
```
TaskService.list_tasks(): 1 + 50 = 51 次查询
EvidenceAgent.execute(): 1 + 20 = 21 次查询
总计: 72 次查询
```

**优化后**:
```
TaskService.list_tasks(): 1 次查询
EvidenceAgent.execute(): 1 次查询
总计: 2 次查询
```

**性能提升**: ~36 倍

## 最佳实践

### 1. 使用 Eager Loading (JOIN)

```python
# ❌ 不好: N+1 查询
for risk in risks:
    clause = await session.get(Clause, risk.clause_id)

# ✅ 好: 使用 JOIN
query = select(Risk, Clause).join(Clause, Risk.clause_id == Clause.clause_id)
result = await session.execute(query)
for risk, clause in result.all():
    # 直接使用已加载的 clause
```

### 2. 使用聚合查询

```python
# ❌ 不好: 多次查询统计
count = await session.execute(select(func.count(Risk.id)))
high_count = await session.execute(select(func.count(Risk.id)).where(Risk.risk_level == "HIGH"))

# ✅ 好: 一次查询获取所有统计
stats = await fetch_one_sql(
    """
    SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE risk_level = 'HIGH') as high_count
    FROM risks
    """
)
```

### 3. 使用 selectinload() 和 joinedload()

对于复杂的关系，可以使用 SQLAlchemy 的 eager loading:

```python
from sqlalchemy.orm import selectinload, joinedload

# 预加载关联对象
query = select(Task).options(
    selectinload(Task.contract_version).selectinload(ContractVersion.contract),
    joinedload(Task.events)
)
```

## 未来优化方向

1. **添加数据库索引**: 为常用的查询条件添加索引
   ```python
   # 在 models.py 中
   __table_args__ = (
       Index("idx_risks_task_clause", "task_id", "clause_id"),
       Index("idx_clauses_task_order", "task_id", "order_no"),
   )
   ```

2. **使用连接池**: SQLite 使用 WAL 模式时的连接池配置
   ```python
   engine = create_async_engine(
       db_url,
       pool_size=10,
       max_overflow=20,
       pool_pre_ping=True,
   )
   ```

3. **查询缓存**: 对频繁查询的静态数据（如 KB collections）添加缓存

4. **批量操作**: 对批量插入/更新使用 `bulk_insert_mappings()` 或 `bulk_update_mappings()`

## 监控

建议添加查询日志监控：

```python
# 在 connection.py 中启用查询日志
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

这样可以观察实际执行的 SQL 查询，发现潜在的性能问题。
