"""
Contract OS Simple - Main FastAPI Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database.connection import init_db, close_db
from .routes import contracts, tasks, kb, health, dashboard
from .rate_limit import limiter, RATE_LIMITS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Contract OS Simple...")
    logger.info(f"Database: {settings.database_path}")
    logger.info(f"Storage: {settings.storage_root}")
    logger.info(f"Max concurrent tasks: {settings.max_concurrent_tasks}")
    logger.info(f"Max API concurrent: {settings.max_api_concurrent}")
    logger.info(f"Rate limiting: {'enabled' if settings.enable_rate_limit else 'disabled'}")
    if settings.enable_rate_limit:
        logger.info(f"  Default rate limit: {settings.rate_limit_per_hour}/hour")

    # Initialize database
    try:
        await init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    # Save all vector stores
    from .utils.vector_store import save_all_vector_stores
    save_all_vector_stores()
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Contract OS Simple",
    description="Contract pre-review system with Python backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(Exception, limiter.exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(contracts.router)
app.include_router(tasks.router)
app.include_router(kb.router)
app.include_router(dashboard.router)
app.include_router(health.router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Contract OS Simple",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
