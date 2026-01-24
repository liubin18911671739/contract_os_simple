# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contract OS Simple is a contract pre-review system that processes contracts through an 8-stage AI-powered pipeline to identify legal risks. This is a Python/FastAPI refactor of an original Node.js system, maintaining 100% API compatibility with the frontend.

**Key Architecture Decisions:**
- **Backend**: Python 3.11+ / FastAPI (replaces Node.js/Fastify)
- **Database**: SQLite + SQLAlchemy async (replaces PostgreSQL + pgvector)
- **Vector Search**: Faiss local indexes (replaces pgvector)
- **Task Queue**: asyncio (replaces BullMQ + Redis)
- **Storage**: Local filesystem (replaces MinIO)
- **LLM**: ZhipuAI API (replaces local vLLM)

## Development Commands

### Environment Setup
```bash
# Create/activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r server/requirements.txt

# Initialize database
python scripts/init_db.py

# Seed sample KB data (optional)
python scripts/seed_kb.py
```

### Running the Application
```bash
# Backend (development mode with auto-reload) - from project root
. .venv/bin/activate
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd client
npm run dev
```

### Database Operations
```bash
# View database tables
sqlite3 data/database.db ".tables"

# Query task events
sqlite3 data/database.db "SELECT * FROM task_events ORDER BY ts DESC LIMIT 10;"

# Reset database
rm data/database.db && python scripts/init_db.py
```

### Testing
```bash
# Run all tests (from project root)
pytest

# Run specific test file
pytest server/tests/test_task_service.py

# Run specific test
pytest server/tests/test_task_service.py::test_create_task

# Run with coverage report
pytest --cov=server --cov-report=html
open htmlcov/index.html  # macOS

# Run performance benchmarks
python server/tests/benchmarks.py
```

**Test Framework Details**:
- Uses `pytest` with `pytest-asyncio` for async test support
- Test fixtures in `server/tests/conftest.py` provide test_db, test_settings, sample data
- Tests use temporary databases (`/tmp/test_db.db`) for isolation
- Set environment variables before imports in conftest.py for test configuration
- Run `pytest server/tests/ -v` for verbose output

### Docker Deployment
```bash
# Build and start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

**Docker Configuration**:
- Multi-stage build in `Dockerfile` (builder + runtime stages)
- Exposes port 8000 for FastAPI
- Volume mounts for data persistence (`./data`, `./storage`)
- Health check endpoint at `/api/health`
- Environment variables loaded from `.env` file

## Architecture

### 8-Stage Task Pipeline

The core of the system is the orchestrator (`server/orchestrator.py`) which runs tasks through these stages:

1. **PARSING** (12%) - Extract text from PDF/DOCX/TXT using `parse_agent.py`
2. **STRUCTURING** (25%) - Split contract into clauses using `split_agent.py`
3. **RULE_SCORING** (37%) - Keyword/regex risk detection using `stub_agents.py`
4. **KB_RETRIEVAL** (50%) - Faiss vector search + ZhipuAI Rerank using `stub_agents.py`
5. **LLM_RISK** (75%) - AI-powered risk analysis using `llm_risk_agent.py` (KEY STAGE)
6. **EVIDENCING** (87%) - Evidence chain collection using `stub_agents.py`
7. **QCING** (95%) - Quality control checks using `stub_agents.py`
8. **DONE** (100%) - Task completion using `stub_agents.py`

**Critical Flow**: When a task is created via `POST /api/precheck-tasks`, the orchestrator is started in background using `asyncio.create_task()`. Each agent receives the task_id and a payload dict that accumulates results from previous stages.

### Agent Base Class

All agents inherit from `BaseAgent` (`server/agents/base.py`):
- `stage_name` property defines the stage name
- `execute()` method implements the stage logic
- `run()` wrapper handles logging, error handling, and progress updates
- Agents use SQLAlchemy async sessions and can access services

### Service Layer Architecture

Services (`server/services/`) are business logic layer:

- **LLMService** (`llm_service.py`) - ZhipuAI client with:
  - `chat()` - Text generation
  - `chat_with_json()` - JSON generation with retry logic
  - `embed()` - Batch embedding generation
  - `rerank()` - Document reranking
  - Concurrency controlled via Semaphore (`MAX_API_CONCURRENT`)

- **KBService** (`kb_service.py`) - Knowledge base with:
  - Faiss vector indexes stored in `data/faiss_indexes/{collection_id}/`
  - Document chunking with configurable size/overlap
  - Hybrid search: Faiss ANN + ZhipuAI Rerank-2

- **TaskService** (`task_service.py`) - Task lifecycle:
  - Creates task with `QUEUED` status
  - Updates progress through stages
  - Logs events to `task_events` table
  - Retrieves KB collection IDs for task

### Database Models

All models defined in `server/database/models.py` using SQLAlchemy declarative base. Key relationships:
- `PrecheckTask` → `ContractVersion` (many-to-one)
- `PrecheckTask` → `Clause` (one-to-many)
- `Clause` → `Risk` (one-to-many)
- `Risk` → `Evidence`, `RuleHit`, `KBCitation` (one-to-many)
- `PrecheckTask` → `TaskKBSnapshot` (one-to-many)

### Vector Storage

Faiss indexes (`server/utils/vector_store.py`):
- One index per KB collection
- Stored in `data/faiss_indexes/{collection_id}/`
- Uses IndexFlatIP (inner product) with normalized vectors
- Metadata (chunk_ids) stored alongside `.faiss` index
- Global registry `_vector_stores` caches indexes in memory

## API Compatibility

**Critical**: All API endpoints must match the original Node.js version exactly. Request/response formats defined in `server/schemas/pydantic_models.py`.

Key endpoints:
- `POST /api/precheck-tasks` - Creates task AND starts orchestrator (returns task ID)
- `GET /api/precheck-tasks/{id}` - Returns task with progress %
- `GET /api/precheck-tasks/{id}/clauses` - Returns clauses with risk info
- `GET /api/precheck-tasks/{id}/events` - Event log for debugging
- `DELETE /api/precheck-tasks/{id}?force=true` - Delete task (force=true cancels running tasks)

## Configuration

Environment variables in `.env`:
- `ZHIPU_API_KEY` - Required for LLM features
- `DATABASE_PATH` - SQLite database location
- `STORAGE_ROOT` - File storage root
- `MAX_CONCURRENT_TASKS` - Max parallel tasks (default: 3)
- `MAX_API_CONCURRENT` - Max parallel API calls (default: 5)
- `TASK_TIMEOUT` - Seconds before stuck task is marked failed (default: 1800)
- `TASK_RECOVERY_INTERVAL` - Seconds between stuck task scans (default: 600)
- `TASK_STARTUP_RECOVERY` - Enable startup recovery of stuck tasks (default: true)

Configuration loaded via `pydantic-settings` in `server/config.py`.

## File Processing

File parsing (`server/utils/file_parser.py`):
- PDF: Uses PyPDF2 (`parse_pdf()`)
- DOCX: Uses python-docx (`parse_docx()`)
- TXT: Handles UTF-8, GBK, GB2312 encodings (`parse_txt()`)
- File storage in `storage/{category}/{path}`

## Error Handling Patterns

1. **Agent failures**: Caught by orchestrator, task marked `FAILED` with error message
2. **LLM JSON parsing failures**: Automatic retry with repair prompt, fallback to `NEEDS_REVIEW` risk
3. **Database errors**: SQLAlchemy async sessions auto-rollback on exception
4. **Cancellation**: Agents check `await self.check_cancelled()` periodically

## Key Dependencies

- `fastapi` + `uvicorn` - Web framework
- `sqlalchemy` + `aiosqlite` - Async ORM
- `faiss-cpu` - Vector similarity search
- `zhipuai` - LLM API client
- `PyPDF2`, `python-docx` - File parsing
- `pydantic` - Data validation
- `greenlet` - Required for SQLAlchemy async

## Important Implementation Notes

1. **Session Management**: Always use `get_session_maker()` context manager for database operations in agents/services
2. **Background Tasks**: Use `asyncio.create_task()` to run orchestrator, don't await
3. **Progress Updates**: Each stage should call `await self.update_progress(task_id, percentage)`
4. **Event Logging**: Use `await self.log_event()` for debugging and audit trail
5. **Vector Indexes**: Call `vector_store.save()` after modifying Faiss indexes
6. **Type Hints**: All functions use Python 3.11+ union syntax (`str | None`)

### Critical: Clause.id vs Clause.clause_id

The `Clause` model has TWO id fields that are easily confused:
- `Clause.id` - The **primary key** (foreign key target for `risks.clause_id`, `kb_hits_temp.clause_id`)
- `Clause.clause_id` - A **business ID** for display purposes (like `clause_abc123`)

**Always use `clause.id`** when creating foreign key relationships:
```python
# CORRECT - uses clause.id (PK)
risk = Risk(clause_id=clause.id, ...)
hit = KBHitTemp(clause_id=clause.id, ...)

# WRONG - causes foreign key constraint errors
risk = Risk(clause_id=clause.clause_id, ...)
```

### Task Deletion and Cancellation

The orchestrator supports force-deleting running tasks:
- `DELETE /api/precheck-tasks/{task_id}?force=true` - Cancels and deletes a running task
- The orchestrator tracks deleted tasks in `deleted_tasks` set to prevent DB updates after deletion
- Agents should call `await self.check_cancelled()` periodically to respect cancellation
- `TaskCancelledException` is raised when a task is cancelled mid-stage

## Common Issues

- **SQLite locked**: Ensure WAL mode enabled (check `connection.py`)
- **Import errors**: Use absolute imports from project root, add to sys.path in scripts
- **LLM rate limits**: Adjust `MAX_API_CONCURRENT` in `.env`
- **Faiss import issues**: Verify numpy version compatibility
- **Agent stuck**: Check event logs via `task_events` table
- **Stuck tasks**: Server restart triggers automatic recovery of tasks stuck >30 minutes (configurable via `TASK_TIMEOUT`)

## Testing Configuration

**Test Database Schema Note**:
- `RuleHit.risk_id` is `nullable=True` to allow rule hits before risks are created
- Test environment variables set in `pytest.ini` and `.env.test`
- Tests use `@pytest.mark.asyncio` for async test functions
- Temporary test databases created per test function for isolation

**Current Test Coverage**:
- `test_task_service.py` - CRUD operations, progress updates, event logging, pagination
- `test_agents.py` - RulesAgent keyword matching
- Benchmarks available in `server/tests/benchmarks.py` for performance testing
