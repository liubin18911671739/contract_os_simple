# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contract OS Simple is a contract pre-review system that processes contracts through a 9-stage AI-powered pipeline to identify legal risks. This is a Python/FastAPI refactor of an original Node.js system, maintaining 100% API compatibility with the frontend.

**Key Architecture Decisions:**
- **Backend**: Python 3.11+ / FastAPI (replaces Node.js/Fastify)
- **Database**: SQLite + SQLAlchemy async (replaces PostgreSQL + pgvector)
- **Vector Search**: Faiss local indexes (replaces pgvector)
- **Task Queue**: asyncio (replaces BullMQ + Redis)
- **Storage**: Local filesystem (replaces MinIO)
- **LLM**: ZhipuAI API (replaces local vLLM)
- **Frontend**: React + TypeScript + Vite + Zustand (state) + React Router

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

# Add database indexes to existing database
python scripts/migrate_add_indexes.py
```

### Running the Application
```bash
# Backend (development mode with auto-reload) - from project root
. .venv/bin/activate
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd client
npm install  # First time only
npm run dev
```

### Frontend Commands
```bash
cd client
npm run dev         # Start dev server (http://localhost:5173)
npm run build       # Production build
npm run lint        # Run ESLint
npm run test        # Run Vitest tests
npm run test:ui     # Run tests with UI
npm run test:coverage # Run tests with coverage report
```

### Database Operations
```bash
# View database tables
sqlite3 data/database.db ".tables"

# Query task events
sqlite3 data/database.db "SELECT * FROM task_events ORDER BY ts DESC LIMIT 10;"

# Reset database
rm data/database.db && python scripts/init_db.py

# Show current indexes
python scripts/migrate_add_indexes.py --show
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
- Backend: `pytest` with `pytest-asyncio` for async test support
- Frontend: `vitest` for unit/integration tests
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

### 9-Stage Task Pipeline

The core of the system is the orchestrator (`server/orchestrator.py`) which runs tasks through these stages:

1. **PARSING** (12%) - Extract text from PDF/DOCX/TXT using `parse_agent.py`
2. **STRUCTURING** (25%) - Split contract into clauses using `split_agent.py`
3. **RULE_SCORING** (37%) - Keyword/regex risk detection using `stub_agents.py`
4. **KB_RETRIEVAL** (50%) - Faiss vector search + ZhipuAI Rerank using `stub_agents.py`
5. **LLM_RISK** (75%) - AI-powered risk analysis using `llm_risk_agent.py` (KEY STAGE)
6. **SUGGESTION** (82%) - Generate modification suggestions using `suggestion_agent.py`
7. **EVIDENCING** (87%) - Evidence chain collection using `stub_agents.py`
8. **QCING** (95%) - Quality control checks using `stub_agents.py`
9. **DONE** (100%) - Task completion using `stub_agents.py`

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
  - **Separate semaphores** for chat/embed/rerank to prevent blocking (chat: 1/2 capacity, embed: 2x capacity, rerank: full capacity)
  - In-memory embedding cache for query vectors (1000 entry LRU cache)

- **KBService** (`kb_service.py`) - Knowledge base with:
  - Faiss vector indexes stored in `data/faiss_indexes/{collection_id}/`
  - Document chunking with configurable size/overlap
  - Hybrid search: Faiss ANN + ZhipuAI Rerank-2
  - Query embedding cache to avoid redundant API calls

- **TaskService** (`task_service.py`) - Task lifecycle:
  - Creates task with `QUEUED` status
  - Updates progress through stages
  - Logs events to `task_events` table
  - Retrieves KB collection IDs for task

- **SuggestionService** (`suggestion_service.py`) - Suggestion and risk management:
  - CRUD operations for modification suggestions
  - Suggestion revision tracking
  - Risk level adjustment with history
  - Evidence chain retrieval

### Database Models

All models defined in `server/database/models.py` using SQLAlchemy declarative base. Key relationships:
- `PrecheckTask` → `ContractVersion` (many-to-one)
- `PrecheckTask` → `Clause` (one-to-many)
- `Clause` → `Risk` (one-to-many)
- `Risk` → `Evidence`, `RuleHit`, `KBCitation`, `Suggestion` (one-to-many)
- `Suggestion` → `SuggestionRevision` (one-to-many)
- `PrecheckTask` → `TaskKBSnapshot` (one-to-many)

**Important**: `KBCitation.chunk_id` is nullable to handle LLM hallucination of invalid chunk IDs. The LLM risk agent validates chunk_ids against actual KB hits before creating citations.

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
- `GET /api/precheck-tasks` - List tasks with pagination, filters, sort
- `GET /api/precheck-tasks/{id}` - Returns task with progress %
- `GET /api/precheck-tasks/{id}/clauses` - Returns clauses with risk info
- `GET /api/precheck-tasks/{id}/events` - Event log for debugging
- `GET /api/precheck-tasks/{id}/summary` - Task summary statistics
- `POST /api/precheck-tasks/{id}/cancel` - Cancel a running task
- `POST /api/precheck-tasks/{id}/conclusion` - Set task conclusion
- `POST /api/precheck-tasks/{id}/report` - Generate/download report
- `DELETE /api/precheck-tasks/{id}?force=true` - Delete task (force=true cancels running tasks)
- `POST /api/precheck-tasks/{id}/retry` - Retry a FAILED or CANCELLED task
- `GET /api/kb/cache-stats` - Embedding cache statistics
- `POST /api/kb/search` - Search knowledge base with reranking
- `GET /api/metrics/overview` - Metrics dashboard data
- `GET /api/metrics/f1-score` - F1 score based on risk confirmation
- `GET /api/metrics/hallucination-rate` - Hallucination rate metrics

### Suggestion API Endpoints

- `GET /api/risks/{risk_id}/suggestions` - Get suggestions for a risk
- `POST /api/risks/{risk_id}/suggestions` - Create new suggestion
- `PUT /api/suggestions/{suggestion_id}` - Update suggestion (creates revision)
- `GET /api/suggestions/{suggestion_id}/revisions` - Get revision history
- `PUT /api/risks/{risk_id}/level` - Adjust risk level
- `GET /api/risks/{risk_id}/evidence-chain` - Get complete evidence chain

## Configuration

Environment variables in `.env`:
- `ZHIPU_API_KEY` - Required for LLM features
- `DATABASE_PATH` - SQLite database location
- `STORAGE_ROOT` - File storage root
- `MAX_CONCURRENT_TASKS` - Max parallel tasks (default: 3)
- `MAX_API_CONCURRENT` - Base max parallel API calls (default: 5)
- `TASK_TIMEOUT` - Seconds before stuck task is marked failed (default: 300)
- `TASK_RECOVERY_INTERVAL` - Seconds between stuck task scans (default: 60)
- `TASK_STARTUP_RECOVERY` - Enable startup recovery of stuck tasks (default: true)
- `ENABLE_RATE_LIMIT` - Enable IP-based rate limiting (default: true)
- `RATE_LIMIT_PER_HOUR` - Default rate limit per IP (default: 200)

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
5. **Invalid chunk_id from LLM**: LLMRiskAgent validates chunk_ids against KB hits, falls back to first available chunk
6. **Rate limiting**: IP-based rate limiting using slowapi (disabled in tests)

## Key Dependencies

**Backend (Python):**
- `fastapi` + `uvicorn` - Web framework
- `sqlalchemy` + `aiosqlite` - Async ORM
- `faiss-cpu` - Vector similarity search
- `zhipuai` - LLM API client
- `slowapi` - Rate limiting
- `PyPDF2`, `python-docx` - File parsing
- `pydantic` - Data validation
- `greenlet` - Required for SQLAlchemy async

**Frontend (Node.js):**
- `react` + `react-dom` - UI framework
- `vite` - Build tool
- `react-router-dom` - Routing
- `zustand` - State management
- `recharts` - Charts
- `lucide-react` - Icons
- `vitest` - Testing framework
- `tailwindcss` - Styling

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
- `POST /api/precheck-tasks/{id}/retry` - Retries FAILED or CANCELLED tasks by resetting to QUEUED and restarting orchestrator

### LLM Risk Agent - Chunk ID Validation

The LLM often returns invalid `chunk_id` values (like descriptive text instead of actual IDs). The agent handles this:
1. Creates a mapping of valid chunk_ids from KB hits before processing
2. Validates LLM-returned chunk_ids against the valid set
3. Falls back to quote text matching if direct match fails
4. Uses first available chunk_id as last resort
5. Only creates KBCitation records with valid chunk_ids

This prevents FOREIGN KEY constraint errors in `kb_citations` table.

### Suggestion Generation Pipeline

The `SuggestionAgent` (`server/agents/suggestion_agent.py`) generates modification suggestions for each risk:
- Runs at SUGGESTION stage (82%) after LLM_RISK completes
- Uses LLM to generate contextual suggestions based on risk summary, KB citations, and rule hits
- Falls back to generic template suggestions if LLM fails
- Batch commits suggestions to database with `created_by='ai'` or `created_by='ai_fallback'`

### Risk Level Adjustment Tracking

Risk level adjustments are tracked through the `qc_flags_json` field on the Risk model:
- `original_risk_level`: Stores the AI-generated level when first adjusted
- `adjusted_at`: Timestamp of adjustment
- `adjusted_by`: User or system that made the adjustment
- `adjustment_reason`: Optional reason for the adjustment

This allows full audit trail of risk level changes.

## Common Issues

- **SQLite locked**: Ensure WAL mode enabled (check `connection.py`)
- **Import errors**: Use absolute imports from project root, add to sys.path in scripts
- **LLM rate limits**: Adjust `MAX_API_CONCURRENT` in `.env` (affects chat/embed/rerank separately)
- **Faiss import issues**: Verify numpy version compatibility
- **Agent stuck**: Check event logs via `task_events` table
- **Stuck tasks**: Server restart triggers automatic recovery of tasks stuck >5 minutes (configurable via `TASK_TIMEOUT`)
- **Foreign key errors on kb_citations**: LLM returned invalid chunk_id - see validation logic in `llm_risk_agent.py`
- **MissingGreenlet errors**: Use `selectinload()` for eager loading in SQLAlchemy queries to prevent lazy loading issues

## Frontend Structure

**Pages** (`client/src/pages/`):
- `Dashboard.tsx` - Main dashboard with stats
- `KBAdmin.tsx` - Knowledge base management
- `NewTaskUpload.tsx` - Create new precheck task
- `Processing.tsx` - Monitor task progress
- `Results.tsx` - View task results and risks (with inline suggestion preview)
- `Review.tsx` - Review and confirm/dismiss risks
- `SuggestionReview.tsx` - Dedicated page for reviewing all suggestions with filtering
- `Evaluation.tsx` - Metrics dashboard (F1, hallucination rate)
- `Settings.tsx` - Application settings

**Components** (`client/src/components/`):
- `ui/` - Reusable UI components (Button, Card, Modal, Table, Badge, etc.)
- `kb/` - Knowledge base specific components (Search, DocumentChunks, etc.)
- `suggestions/` - Suggestion feature components:
  - `EvidenceChain.tsx` - Timeline visualization of complete evidence chain
  - `SuggestionCard.tsx` - Individual suggestion display card
  - `SuggestionEditor.tsx` - Modal editor for editing suggestions
  - `RevisionHistory.tsx` - Revision history viewer with timeline
  - `RiskLevelAdjuster.tsx` - Interactive risk level adjuster
- `layout/` - Layout components (Header, Sidebar, MainLayout)

**State Management**: Zustand stores in `client/src/api/` for API communication

**Frontend API Client** (`client/src/api/`):
- `http.ts` - HTTP client with get/post/put/del methods and logging
- `tasks.ts` - Task-related API calls
- `suggestions.ts` - Suggestion and evidence chain API calls

## Testing Configuration

**Test Database Schema Note**:
- `RuleHit.risk_id` is `nullable=True` to allow rule hits before risks are created
- `KBCitation.chunk_id` is `nullable=True` to handle LLM hallucination
- Test environment variables set in `pytest.ini` and `.env.test`
- Tests use `@pytest.mark.asyncio` for async test functions
- Temporary test databases created per test function for isolation

**Current Test Coverage**:
- `test_task_service.py` - CRUD operations, progress updates, event logging, pagination
- `test_agents.py` - RulesAgent keyword matching
- `test_integration.py` - Full pipeline integration tests
- Benchmarks available in `server/tests/benchmarks.py` for performance testing
