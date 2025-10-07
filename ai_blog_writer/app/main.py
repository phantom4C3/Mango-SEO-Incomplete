# ai_blog_writer/src/app/main.py
import logging
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .middleware.rate_limiter import RedisRateLimiterMiddleware
from .core.exceptions import FormatterError, PipelineError, IntegrationError
from .clients.redis_client import redis_client
from .clients.supabase_client import supabase_client
from .api.endpoints.generate_blog import router as generate_blog_router
from .api.endpoints.suggest_blog_topics import router as suggest_topics_router
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_blog_writer")


# Print environment loading info at startup
print("🔍 [main.py] .env loaded?")
print(f"🔍 [main.py] GEMINI_API_KEY: {settings.gemini_api_key}")
print(f"🔍 [main.py] SUPABASE_URL: {settings.supabase_url}")
print(f"🔍 [main.py] SUPABASE_SERVICE_ROLE_KEY: {settings.supabase_service_role_key}")

# -----------------------------
# Async helpers
# -----------------------------
async def async_supabase_connect():
    await asyncio.to_thread(supabase_client.connect)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI Blog Writer starting up...")

    try:
        await redis_client.connect()
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect Redis: {e}")

    try:
        await async_supabase_connect()
        logger.info("✅ Supabase connected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Supabase connect failed: {e}")

    yield

    logger.info("🛑 AI Blog Writer shutting down...")
    try:
        await redis_client.disconnect()
        logger.info("✅ Redis disconnected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis disconnect failed: {e}")


# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="MangoSEO AI Blog Writer",
    description="AI-powered blog content generation service",
    version="1.0.0",
    lifespan=lifespan,
)

# -----------------------------
# Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RedisRateLimiterMiddleware, max_requests=50, window_seconds=60)

# -----------------------------
# Exception Handlers
# -----------------------------
async def custom_exceptions_handler(request: Request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

app.add_exception_handler(FormatterError, custom_exceptions_handler)
app.add_exception_handler(PipelineError, custom_exceptions_handler)
app.add_exception_handler(IntegrationError, custom_exceptions_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": exc.errors(),
            "body": getattr(exc, "body", None),
        },
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "message": exc.detail},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": str(exc)},
    )

# -----------------------------
# Health Endpoints
# -----------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-blog-writer"}

# -----------------------------
# Routers
# -----------------------------
app.include_router(generate_blog_router, prefix="/blog", tags=["Blog"])
app.include_router(suggest_topics_router, prefix="/blog", tags=["Blog"])

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host or "127.0.0.1",
        port=settings.port or 8000,
        reload=bool(settings.debug),
    )
