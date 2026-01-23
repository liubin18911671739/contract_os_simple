"""
Contract OS Simple - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from server.config import settings
from server.database.connection import close_db, init_db
from server.rate_limit import RATE_LIMITS, limiter
from server.routes import contracts, dashboard, health, kb, metrics, tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
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
    logger.info(
        f"Rate limiting: {'enabled' if settings.enable_rate_limit else 'disabled'}"
    )
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
    from server.utils.vector_store import save_all_vector_stores

    save_all_vector_stores()
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Contract OS Simple",
    description="Contract pre-review system with Python backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Add rate limiter to app state (if enabled)
if settings.enable_rate_limit:
    app.state.limiter = limiter

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
app.include_router(metrics.router)
app.include_router(health.router)


# Custom docs endpoints with better error handling
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse


@app.get("/openapi.json", include_in_schema=False)
async def openapi():
    """Get OpenAPI schema"""
    return JSONResponse(get_openapi(title=app.title, version=app.version, routes=app.routes))


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with fallback"""
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head>
    <title>Contract OS Simple - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; padding: 0; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
        .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                defaultModelsExpandDepth: 0,
                tryItOutEnabled: true
            });
            window.ui = ui;
        };
    </script>
</body>
</html>""")


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc HTML"""
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head>
    <title>Contract OS Simple - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <redoc spec-url="/openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body>
</html>""")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    # Skip Chrome DevTools requests
    if ".well-known" in request.url.path:
        return await call_next(request)

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
