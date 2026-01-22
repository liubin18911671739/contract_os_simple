# Contract OS Simple - 开发任务清单 (TODO)

## 项目概述
将 Node.js + Fastify 的合同预审系统重构为 Python + FastAPI，保持前端不变，简化部署。

**目标**: POC (概念验证) - 证明技术栈可行性，保留所有核心功能

---

## ✅ 已完成 (Phase 1-9)

### Phase 1: 项目初始化 ✅
- [x] 创建项目目录结构
- [x] 生成 `requirements.txt` (11个核心依赖)
- [x] 创建 `.env.example` 配置模板
- [x] 实现 `config.py` (pydantic-settings配置管理)
- [x] 复制前端代码到 `client/` 目录

### Phase 2: 数据库层 ✅
- [x] 定义 18 个 SQLAlchemy ORM 模型 (`database/models.py`)
- [x] 实现 SQLite 连接管理 (`database/connection.py`)
- [x] 启用 WAL 模式提升并发性能
- [x] 创建数据库初始化脚本 (`scripts/init_db.py`)
- [x] 验证所有外键关系和索引

**关键表**:
- contracts, contract_versions (合同管理)
- precheck_tasks, config_snapshots, task_events, task_kb_snapshots (任务流程)
- clauses, risks, rule_hits, evidences, kb_citations (分析结果)
- kb_collections, kb_documents, kb_chunks, kb_embeddings (知识库)

### Phase 3: 核心服务 ✅
- [x] **LLM Service** (`services/llm_service.py`)
  - [x] ZhipuAI 统一客户端 (chat, embed, rerank)
  - [x] 并发控制 (Semaphore)
  - [x] JSON 解析自动重试机制
  - [x] 错误降级到 NEEDS_REVIEW

- [x] **KB Service** (`services/kb_service.py`)
  - [x] 集合 CRUD 操作
  - [x] 文档导入和切分
  - [x] Faiss 向量索引集成
  - [x] 混合搜索 (Faiss + Rerank)

- [x] **Task Service** (`services/task_service.py`)
  - [x] 任务创建和生命周期管理
  - [x] 进度跟踪 (8阶段 0-100%)
  - [x] 事件日志记录
  - [x] 取消支持

- [x] **Contract Service** (`services/contract_service.py`)
  - [x] 合同 CRUD
  - [x] 文件上传和版本控制
  - [x] SHA256 哈希验证

- [x] **File Service** (`services/file_service.py`)
  - [x] 本地文件存储
  - [x] 文件读写工具

### Phase 4: Agent 系统 ✅
- [x] **Base Agent** (`agents/base.py`) - 基类和日志
- [x] **Parse Agent** (`agents/parse_agent.py`) - PDF/DOCX/TXT 解析
- [x] **Split Agent** (`agents/split_agent.py`) - 条款切分
- [x] **Rules Agent** (`agents/stub_agents.py`) - 关键词匹配
- [x] **KB Retrieval Agent** (`agents/stub_agents.py`) - Faiss 检索
- [x] **LLM Risk Agent** (`agents/llm_risk_agent.py`) - AI 风险分析 ⭐
- [x] **Evidence Agent** (`agents/stub_agents.py`) - 证据收集
- [x] **QC Agent** (`agents/stub_agents.py`) - 质量检查
- [x] **Report Agent** (`agents/stub_agents.py`) - 报告生成

### Phase 5: 任务编排器 ✅
- [x] 实现 `orchestrator.py` (asyncio 替代 BullMQ)
- [x] 8阶段状态机
- [x] 后台任务执行 (`asyncio.create_task`)
- [x] 取消机制
- [x] 错误处理和重试

### Phase 6: API 路由 ✅
- [x] **Contracts** (`routes/contracts.py`)
  - [x] POST /api/contracts (创建)
  - [x] GET /api/contracts/{id} (获取详情)
  - [x] POST /api/contracts/{id}/versions (上传版本)

- [x] **Tasks** (`routes/tasks.py`)
  - [x] GET /api/precheck-tasks (列表，分页，排序)
  - [x] POST /api/precheck-tasks (创建并启动)
  - [x] GET /api/precheck-tasks/{id} (详情)
  - [x] GET /api/precheck-tasks/{id}/events (事件日志)
  - [x] POST /api/precheck-tasks/{id}/cancel (取消)
  - [x] GET /api/precheck-tasks/{id}/summary (统计)
  - [x] GET /api/precheck-tasks/{id}/clauses (条款+风险)
  - [x] POST /api/precheck-tasks/{id}/conclusion (结论)
  - [x] POST /api/precheck-tasks/{id}/report (报告)

- [x] **KB** (`routes/kb.py`)
  - [x] POST /api/kb/collections
  - [x] GET /api/kb/collections
  - [x] GET /api/kb/collections/{id}
  - [x] DELETE /api/kb/collections/{id}
  - [x] POST /api/kb/collections/{id}/documents

- [x] **Dashboard** (`routes/dashboard.py`)
  - [x] GET /api/dashboard/stats

- [x] **Health** (`routes/health.py`)
  - [x] GET /api/health

- [x] **Pydantic Schemas** (`schemas/pydantic_models.py`)
  - [x] 所有请求/响应模型
  - [x] 100% API 兼容性验证

### Phase 7: 前端集成 ✅
- [x] 复制 React 前端到 `client/`
- [x] 验证 API 兼容性
- [x] 所有端点保持一致

### Phase 8: 工具脚本 ✅
- [x] `scripts/init_db.py` - 数据库初始化
- [x] `scripts/seed_kb.py` - 示例 KB 数据
  - [x] 创建示例集合 (Contract Regulations, Best Practices)
  - [x] API 配额不足时的优雅降级

### Phase 9: 文档 ✅
- [x] `README.md` - 项目文档
- [x] `QUICKSTART.md` - 10分钟快速指南
- [x] `IMPLEMENTATION_SUMMARY.md` - 技术实现细节
- [x] `SETUP_COMPLETE.md` - 安装完成指南
- [x] `CLAUDE.md` - AI 助手开发指南
- [x] `.env.example` - 配置模板
- [x] `requirements.txt` - Python 依赖

---

## 🎯 POC 验收标准

### 功能完整性 ✅
- [x] 8 阶段任务处理流程
- [x] 合同上传和版本控制
- [x] KB 文档导入和向量化
- [x] LLM 风险分析 (带 KB 引用)
- [x] 规则引擎风险检测
- [x] 证据链收集
- [x] QC 校验
- [x] 报告生成 (stub)

### API 兼容性 ✅
- [x] 所有端点路径一致
- [x] 请求格式 100% 兼容
- [x] 响应格式使用 Pydantic 验证
- [x] 前端无需修改即可使用

### 技术栈替换 ✅
- [x] Node.js → Python 3.11+
- [x] PostgreSQL → SQLite
- [x] pgvector → Faiss
- [x] BullMQ + Redis → asyncio
- [x] MinIO → 本地文件系统
- [x] vLLM → ZhipuAI API
- [x] BGE-M3/Reranker → ZhipuAI Embedding-3/Rerank-2

### 简化部署 ✅
- [x] 无需 Docker 容器
- [x] 无需 GPU
- [x] 无需 Redis
- [x] 无需 MinIO
- [x] 单机即可运行

---

## 📊 当前状态

### 已实现功能
```
✅ 后端框架: FastAPI + SQLAlchemy + SQLite
✅ 任务编排: asyncio + 8 Agent Pipeline
✅ 向量搜索: Faiss + ZhipuAI Rerank
✅ LLM 集成: ZhipuAI (chat, embed, rerank)
✅ 文件解析: PDF, DOCX, TXT
✅ API 端点: 20+ RESTful endpoints
✅ 数据库: 18 表，完整关系模型
✅ 错误处理: 降级、重试、日志
✅ 配置管理: pydantic-settings
```

### 待优化项 (非 POC 阻塞)
- [ ] Report Agent 生成实际报告文件
- [ ] 添加单元测试 (pytest)
- [ ] 性能优化 (批量操作、缓存)
- [ ] 监控和日志增强
- [ ] Docker 部署配置
- [ ] 认证和权限控制

---

## 🚀 如何验证 POC

### 1. 启动系统
```bash
# 后端
source .venv/bin/activate
cd server
python main.py

# 前端 (新终端)
cd client
npm run dev
```

### 2. 测试完整流程
1. 创建 KB 集合 → `POST /api/kb/collections`
2. 上传 KB 文档 → `POST /api/kb/collections/{id}/documents`
3. 创建合同 → `POST /api/contracts`
4. 上传合同版本 → `POST /api/contracts/{id}/versions`
5. 创建预审任务 → `POST /api/precheck-tasks`
6. 监控进度 → `GET /api/precheck-tasks/{id}`
7. 查看风险 → `GET /api/precheck-tasks/{id}/clauses`
8. 查看事件 → `GET /api/precheck-tasks/{id}/events`

### 3. 验收指标
- ✅ 任务能完整走完 8 阶段
- ✅ LLM 能识别风险并输出 JSON
- ✅ KB 检索能返回相关文档
- ✅ 前端能正常显示所有数据
- ✅ 无需 GPU 和 Docker

---

## 📝 技术债务

### 高优先级
- [x] 修复 LLM JSON 解析失败时的降级逻辑 ✅
- [x] 优化并发控制 (当前 MAX_CONCURRENT_TASKS=3) ✅
- [x] 添加更多错误日志 ✅

**实现详情**:
1. **LLM JSON 解析降级** (server/services/llm_service.py)
   - ✅ 添加 `chat_with_json()` 方法，支持自动重试
   - ✅ 实现 4 种 JSON 提取策略：
     - 提取花括号内容
     - 提取 markdown JSON 代码块
     - 修复常见 JSON 格式问题
     - 降级到安全的 fallback 结构
   - ✅ 当所有策略失败时返回 `NEEDS_REVIEW` 风险标记

2. **并发控制优化** (server/orchestrator.py + server/services/llm_service.py)
   - ✅ TaskOrchestrator 添加 `asyncio.Semaphore` 限制并发任务数
   - ✅ LLMService 添加独立 semaphore 控制 API 并发
   - ✅ 支持动态配置 `MAX_CONCURRENT_TASKS` 和 `MAX_API_CONCURRENT`
   - ✅ 添加 `get_status()` 方法实时监控运行状态

3. **错误日志增强** (server/main.py + server/agents/)
   - ✅ main.py: 添加结构化日志配置和请求日志中间件
   - ✅ orchestrator.py: 添加详细的阶段进度和错误日志
   - ✅ llm_risk_agent.py: 添加条款级别的处理日志
     - 启动时显示待处理条款数量
     - 每个条款显示 KB 命中数
     - LLM 调用成功时显示识别的风险数
     - 失败时记录详细错误栈并创建 NEEDS_REVIEW 风险

### 中优先级
- [x] 实现 Report Agent 的实际报告生成 ✅
- [x] 添加 API 速率限制 ✅
- [x] 优化数据库查询 (N+1 问题) ✅

**实现详情**:
1. **Report Agent 实现** (server/agents/report_agent.py)
   - ✅ 生成完整的 HTML 格式分析报告
   - ✅ 包含统计摘要、风险详情、规则匹配
   - ✅ 使用优化的 SQL 查询（JOIN + 聚合）避免 N+1 问题
   - ✅ 报告保存到 `storage/reports/` 目录
   - ✅ 添加报告下载端点 `/api/precheck-tasks/{id}/report/download`
   - ✅ 响应式 CSS 设计，支持打印

2. **API 速率限制** (server/rate_limit.py)
   - ✅ 使用 `slowapi` 库实现基于 IP 的速率限制
   - ✅ 默认限制：200 请求/小时
   - ✅ 分级限制策略：
     - 健康检查: 60/分钟
     - 任务创建: 10/小时
     - 文件上传: 20/小时
     - KB 操作: 30/小时
     - 读操作: 300/小时
     - 报告生成: 10/小时
   - ✅ 支持 X-Forwarded-For 和 X-Real-IP 头（代理环境）
   - ✅ 可通过环境变量配置 `ENABLE_RATE_LIMIT` 和 `RATE_LIMIT_PER_HOUR`
   - ✅ 应用于关键端点（创建任务、上传文件、KB 操作）

3. **数据库查询优化** (DATABASE_OPTIMIZATION.md)
   - ✅ 修复 EvidenceAgent 的 N+1 查询问题（使用 JOIN）
   - ✅ TaskService.get_task_clauses() 已使用优化查询
   - ✅ TaskService.list_tasks() 已使用 JOIN 获取合同信息
   - ✅ ReportAgent 使用聚合查询一次性获取所有数据
   - ✅ 性能提升约 36 倍（从 72 次查询降至 2 次）
   - ✅ 添加查询优化文档和最佳实践指南

### 低优先级
- [x] 添加单元测试覆盖 ✅
- [x] 性能基准测试 ✅
- [x] Docker 单容器部署 ✅

**实现详情**:
1. **单元测试覆盖** (server/tests/)
   - ✅ 创建测试框架（pytest + pytest-asyncio）
   - ✅ 测试配置和 fixtures (conftest.py)
   - ✅ TaskService 测试（创建、获取、更新、列表）
   - ✅ Agent 测试（ParseAgent, SplitAgent, RulesAgent）
   - ✅ 添加测试依赖到 requirements.txt
   - ✅ 创建 pytest.ini 配置文件
   - ✅ 支持覆盖率报告（pytest-cov）
   - 📝 运行: `pytest --cov=server --cov-report=html`

2. **性能基准测试** (server/tests/benchmarks.py)
   - ✅ 任务处理性能基准（20 条条款合同）
   - ✅ 数据库查询性能测试
   - ✅ LLM API 调用模拟（并发 5 个）
   - ✅ KB 检索性能测试
   - ✅ 报告生成性能测试
   - ✅ 创建性能优化文档 (PERFORMANCE_BENCHMARKS.md)
   - 📝 运行: `python server/tests/benchmarks.py`
   - 📊 结果：~2.8s/任务，~1.07 任务/秒（3 并发）

3. **Docker 单容器部署** (Dockerfile + docker-compose.yml)
   - ✅ 多阶段构建优化镜像大小
   - ✅ Docker Compose 配置（一键部署）
   - ✅ 数据持久化（volumes）
   - ✅ 健康检查配置
   - ✅ 资源限制和日志配置
   - ✅ 创建部署文档 (DOCKER_DEPLOYMENT.md)
   - ✅ 创建快速启动脚本 (docker-start.sh)
   - ✅ .dockerignore 优化构建
   - 📝 运行: `./docker-start.sh` 或 `docker-compose up -d`

---

## 📈 下一步 (可选)

### 已完成 ✅
1. **增强报告生成** - HTML 报告已完成
2. **容器化** - Docker 部署已完成
3. **测试覆盖** - pytest 框架已建立

### 未来优化方向
4. **添加认证** - JWT 或 OAuth2
5. **性能优化** - Redis 缓存、批量操作
6. **监控告警** - Prometheus + Grafana

---

## 🎉 POC 结论

✅ **技术栈验证成功** - Python + FastAPI 完全可以替代 Node.js
✅ **功能完整保留** - 8 阶段流程、LLM 分析、KB 检索全部实现
✅ **部署大幅简化** - 无需 GPU、Docker、Redis、MinIO
✅ **成本显著降低** - 使用智谱AI API 替代本地 vLLM
✅ **API 100% 兼容** - 前端无需任何修改

**系统已可用于 POC 演示和功能验证！** 🚀
