# Contract OS Simple

一个简化的合同预审系统，采用 Python/FastAPI 后端和 React 前端。

## 概述

这是对原始 Node.js 版本 Contract OS 系统的重构，具有以下技术栈变更：

### 后端替换
```diff
- Node.js + Fastify + TypeScript
+ Python 3.11+ + FastAPI

- PostgreSQL + pgvector
+ SQLite + Faiss (本地向量索引)

- BullMQ + Redis (消息队列)
+ asyncio.Queue (内存队列)

- MinIO (对象存储)
+ 本地文件系统

- 本地 vLLM (3个Docker容器，需要GPU)
+ 智谱AI API (无需GPU)

- BGE-M3 向量化 (本地)
+ 智谱AI Embedding-3 API

- BGE-Reranker (本地)
+ 智谱AI Rerank-2 API
```

### 前端保持不变
- ✅ React + Vite + TailwindCSS
- ✅ 所有页面和组件
- ✅ API 客户端代码
- ✅ UI/UX 设计

## 功能特性

- ✅ 合同管理与版本控制
- ✅ 知识库管理与文档导入
- ✅ 8 阶段任务处理流程
  1. **PARSING** - 从 PDF/DOCX/TXT 提取文本
  2. **STRUCTURING** - 将合同分割为条款
  3. **RULE_SCORING** - 基于关键词/正则的风险检测
  4. **KB_RETRIEVAL** - Faiss 向量搜索 + 智谱AI Rerank
  5. **LLM_RISK** - AI 驱动的风险分析
  6. **EVIDENCING** - 证据链收集
  7. **QCING** - 质量控制检查
  8. **DONE** - 任务完成
- ✅ 带证据和 KB 引用的风险分析
- ✅ 报告生成

## 项目结构

```
contract_os_simple/
├── server/                    # Python FastAPI 后端
│   ├── main.py               # 应用入口
│   ├── config.py             # 配置管理
│   ├── requirements.txt      # Python 依赖
│   ├── database/             # SQLAlchemy ORM 模型
│   │   ├── connection.py     # SQLite 连接
│   │   └── models.py         # 18 个数据库表
│   ├── services/             # 业务逻辑
│   │   ├── llm_service.py    # 智谱AI 客户端
│   │   ├── kb_service.py     # 知识库 + Faiss
│   │   ├── task_service.py   # 任务管理
│   │   ├── contract_service.py # 合同管理
│   │   └── file_service.py   # 文件存储
│   ├── agents/               # 8 个处理代理
│   │   ├── base.py           # Agent 基类
│   │   ├── parse_agent.py    # 文件解析
│   │   ├── split_agent.py    # 条款切分
│   │   ├── llm_risk_agent.py # LLM 风险分析
│   │   └── stub_agents.py    # 其他 Agent
│   ├── orchestrator.py       # 任务编排器
│   ├── routes/               # API 端点
│   │   ├── contracts.py
│   │   ├── tasks.py
│   │   ├── kb.py
│   │   ├── dashboard.py
│   │   └── health.py
│   ├── schemas/              # Pydantic 模型
│   │   └── pydantic_models.py
│   └── utils/                # 工具函数
│       ├── file_parser.py    # PDF/DOCX 解析
│       └── vector_store.py   # Faiss 包装器
├── client/                   # React 前端（从原版复制）
├── storage/                  # 本地文件存储
│   ├── contracts/
│   ├── kb_documents/
│   └── reports/
├── data/                     # 运行时数据
│   ├── database.db          # SQLite 数据库
│   └── faiss_indexes/       # Faiss 向量索引
├── scripts/                  # 工具脚本
│   ├── init_db.py           # 数据库初始化
│   └── seed_kb.py           # 示例 KB 数据
├── .env.example
└── README.md
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+ (用于前端)
- 智谱AI API 密钥

### 后端设置

1. **创建并激活虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **安装依赖**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp ../.env.example ../.env
   # 编辑 .env 并添加你的 ZHIPU_API_KEY
   ```

4. **初始化数据库**
   ```bash
   cd ..
   python scripts/init_db.py
   ```

5. **（可选）初始化示例 KB 数据**
   ```bash
   python scripts/seed_kb.py
   ```
   这将创建两个示例知识库集合：
   - Contract Regulations
   - Contract Best Practices

   **注意**: 如果 API 余额不足，集合仍会被创建，但文档不会导入 embedding。你可以稍后通过 API 或 UI 导入。

6. **启动后端**
   ```bash
   cd server
   python main.py
   ```

   后端将运行在 `http://localhost:8000`

   API 文档: `http://localhost:8000/docs`

### 前端设置（新终端）

1. **复制前端代码**
   ```bash
   # 如果还没复制，从原项目复制
   cp -r /path/to/contract_os/client ./client
   ```

2. **安装依赖**
   ```bash
   cd client
   npm install
   ```

3. **启动前端**
   ```bash
   npm run dev
   ```

   前端将运行在 `http://localhost:5173`

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest server/tests/test_task_service.py

# 运行测试并生成覆盖率报告
pytest --cov=server --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
```

**注意**: 测试会自动使用测试环境变量，无需配置 `.env` 文件。

详细的测试指南请参考 [TEST_GUIDE.md](TEST_GUIDE.md)。

## API 端点

所有端点与原 Node.js 版本完全兼容：

### 合同
- `POST /api/contracts` - 创建合同
- `GET /api/contracts/{id}` - 获取合同详情及版本
- `POST /api/contracts/{id}/versions` - 上传合同版本

### 任务
- `GET /api/precheck-tasks` - 列表任务（分页、筛选、排序）
- `POST /api/precheck-tasks` - 创建任务
- `GET /api/precheck-tasks/{id}` - 获取任务详情
- `GET /api/precheck-tasks/{id}/events` - 获取任务事件
- `POST /api/precheck-tasks/{id}/cancel` - 取消任务
- `GET /api/precheck-tasks/{id}/summary` - 获取任务统计
- `GET /api/precheck-tasks/{id}/clauses` - 获取任务条款
- `POST /api/precheck-tasks/{id}/conclusion` - 设置结论
- `POST /api/precheck-tasks/{id}/report` - 生成报告

### 知识库
- `POST /api/kb/collections` - 创建 KB 集合
- `GET /api/kb/collections` - 列出集合
- `GET /api/kb/collections/{id}` - 获取集合详情
- `DELETE /api/kb/collections/{id}` - 删除集合
- `POST /api/kb/collections/{id}/documents` - 导入文档

### 仪表盘
- `GET /api/dashboard/stats` - 获取仪表盘统计

### 健康检查
- `GET /api/health` - 健康检查

## 配置

`.env` 文件中的环境变量：

```bash
# 智谱AI 配置
ZHIPU_API_KEY=your-key-here
ZHIPU_CHAT_MODEL=glm-4-flash
ZHIPU_EMBED_MODEL=embedding-3
ZHIPU_RERANK_MODEL=rerank-2

# 数据库
DATABASE_PATH=./data/database.db

# 存储
STORAGE_ROOT=./storage

# 服务器
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# 并发
MAX_CONCURRENT_TASKS=3
MAX_API_CONCURRENT=5
```

## 开发

### 运行测试
```bash
cd server
pytest tests/
```

### 数据库管理
```bash
# 初始化/重置数据库
python scripts/init_db.py

# 查看数据库（使用 sqlite3）
sqlite3 data/database.db
```

### 监控
- 在数据库的 `task_events` 表中查看任务日志
- 检查 Faiss 索引: `ls -la data/faiss_indexes/`
- 监控存储: `ls -la storage/`

## 性能

- **单任务处理时间**: < 5 分钟
- **并发任务数**: 最多 3 个（可配置）
- **知识库检索**: < 2 秒
- **数据库**: 支持百万级记录（SQLite with WAL）

## 故障排除

### SQLite 锁定错误
如果遇到 "database is locked" 错误：
- WAL 模式默认已启用
- 如需要可增加 `MAX_CONCURRENT_TASKS`
- 检查是否有长事务

### LLM API 错误
- 检查 `ZHIPU_API_KEY` 是否有效
- 验证 API 配额/余额
- 如被限流可调整 `MAX_API_CONCURRENT`

### 导入错误
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 检查 Python 版本（需要 3.11+）
python --version
```

## 从 Node.js 版本迁移

API 完全兼容。迁移步骤：

1. 从 PostgreSQL 导出数据（如需要）
2. 导入到 SQLite（使用相同的 schema）
3. 更新前端 API 基础 URL 为 `http://localhost:8000`
4. 测试所有工作流程

## 许可证

与原 Contract OS 项目相同。

## 支持

如有问题或疑问，请参考原项目文档或创建 issue。

## 相关文档

### 核心文档
- [DEVELOPMENT_GUIDE.md](./docs/DEVELOPMENT_GUIDE.md) - 完整的开发指南（开发环境配置、架构说明、最佳实践）
- [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) - 部署指南（Docker、云平台、生产环境配置）
- [API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) - API 文档（所有端点、请求/响应格式、示例）
- [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) - 故障排除指南（常见问题诊断和解决方案）

### 其他文档
- [TODO.md](./TODO.md) - 开发任务和 POC 验收标准
- [QUICKSTART.md](./docs/QUICKSTART.md) - 10 分钟快速指南
- [IMPLEMENTATION_SUMMARY.md](./docs/IMPLEMENTATION_SUMMARY.md) - 技术实现细节
- [SETUP_COMPLETE.md](./docs/SETUP_COMPLETE.md) - 安装完成指南
- [CLAUDE.md](./CLAUDE.md) - AI 助手开发指南
- [TEST_GUIDE.md](./docs/TEST_GUIDE.md) - 测试指南
