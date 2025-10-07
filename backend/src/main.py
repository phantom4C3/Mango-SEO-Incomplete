# backend/src/main.py
import asyncio
import uvicorn 
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional

# Correct imports based on folder structure
from .api.v1 import api_router
from .core.config import settings
from .core.app_logging  import configure_logging
from .services.blog_generation_service import blog_generation_service

from .middleware.rate_limiter import RateLimitMiddleware 
from .clients.supabase_client import supabase_client
from .services.realtime_listener_service import realtime_listener_service

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MangoSEO API",
    description="API for MangoSEO platform (orchestrated AI content, SEO, and CMS integrations)",
    version="1.0.0",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


app.add_middleware(RateLimitMiddleware)


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root health check
@app.get("/", tags=["health"])
async def root_health():
    return {"status": "ok", "message": "MangoSEO API is running."}


# --- Startup & Shutdown hooks ---
from .clients.supabase_client import AsyncSupabaseClient

supabase_client: Optional[AsyncSupabaseClient] = None

@app.on_event("startup")
async def startup_event():
    global supabase_client
    supabase_client = AsyncSupabaseClient()
    supabase_client.connect()
    
    # Start other services
    await blog_generation_service.initialize()
    asyncio.create_task(realtime_listener_service.start_listening())
    logger.info("Realtime listener started on app startup")



@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    await blog_generation_service.shutdown()

    # ✅ Stop realtime listener gracefully
    await realtime_listener_service.stop_listening()
    logger.info("Realtime listener stopped on app shutdown")
