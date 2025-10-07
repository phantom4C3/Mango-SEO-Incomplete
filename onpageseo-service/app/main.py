# onpageseo-service/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
import asyncio

from .middleware.rate_limiter import RateLimiterMiddleware
from .api.v1.endpoints.analyze import router as analyze_router
from .clients.redis_client import redis_client
from .clients.supabase_client import supabase_client
from .core.config import get_settings
 
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings (cached singleton)
settings = get_settings()


async def async_supabase_connect():
    """Async wrapper for Supabase connect to avoid blocking the event loop."""
    await asyncio.to_thread(supabase_client.connect)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info("On-Page SEO Service starting up...")

    # Connect Redis
    try:
        await redis_client.connect()
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect Redis at startup: {e}")

    # Connect Supabase (async-safe)
    try:
        await async_supabase_connect()
        logger.info("✅ Supabase connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect Supabase at startup: {e}")

    yield  # Application is running here

    # Shutdown
    logger.info("On-Page SEO Service shutting down...")
    try:
        await redis_client.disconnect()
        logger.info("✅ Redis disconnected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis disconnect failed: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MangoSEO On-Page SEO Service",
        description="API for on-page SEO analysis and recommendations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ correct
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    print("🚀 CORS Origins (onpageseo):", settings.backend_cors_origins)


    # Add rate limiting middleware
    app.add_middleware(RateLimiterMiddleware)

    # Include API routers
    app.include_router(analyze_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": "1.0.0",
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "MangoSEO On-Page SEO Service",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "analyze": "/seo/analyze",
                "batch_analyze": "/seo/analyze/batch",
            },
        }

    return app


# Create the FastAPI application instance
app = create_app()


