# backend/src/api/v1/endpoints/health.py
"""
Health Check Endpoints
API endpoints for monitoring application health and service status.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import time
import httpx

from ....core.config import settings

from ....clients.supabase_client import supabase_client


router = APIRouter()

# Global start time for uptime calculation
start_time = time.time()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    Returns simple status indicating the API is running.
    """
    return {"status": "healthy", "message": "API is running"}


@router.get("/health/detailed", response_model=Dict[str, object])
async def detailed_health_check() -> Dict[str, object]:
    """
    Detailed health check including database and external services.
    AI worker is not included (checked independently).
    """
    health_status: Dict[str, object] = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {},
    }

    # Check Supabase database connection
    db_status = await _check_database_health()
    health_status["services"]["database"] = db_status

    # Check external APIs if configured
    if getattr(settings, "LEMONSQUEEZY_API_KEY", None):
        lemon_squeezy_status = await _check_lemon_squeezy_health()
        health_status["services"]["lemon_squeezy"] = lemon_squeezy_status

    # Determine overall status
    all_healthy = all(
        service.get("status") == "healthy"
        for service in health_status["services"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    return health_status


@router.get("/health/readiness", response_model=Dict[str, str])
async def readiness_probe() -> Dict[str, str]:
    """
    Readiness probe for Kubernetes/container orchestration.
    Checks only database connectivity.
    """
    try:
        # fetch_one now uses limit=1 internally, very efficient
        await supabase_client.fetch_one("users", select="count")
        return {"status": "ready", "message": "Application is ready to receive traffic"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "message": f"Service not ready: {str(e)}"},
        )



@router.get("/health/liveness", response_model=Dict[str, str])
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/container orchestration.
    Indicates whether the application is running.
    """
    return {"status": "alive", "message": "Application is running"}


async def _check_database_health() -> Dict[str, object]:
    """
    Check database connection health.
    """
    try:
        start = time.time()
        # Use fetch_one with select="count" for efficient counting
        response = await supabase_client.fetch_one("users", select="count")

        return {
            "status": "healthy",
            "response_time_ms": round((time.time() - start) * 1000, 2),
            "details": {
                "connected": True,
                "query_successful": True,
                "row_count": getattr(response, "count", 0),
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": {"connected": False, "query_successful": False},
        }



async def _check_lemon_squeezy_health() -> Dict[str, object]:
    """
    Check Lemon Squeezy API health.
    """
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.LEMONSQUEEZY_API_KEY}",
                "Accept": "application/vnd.api+json",
            }
            response = await client.get(
                "https://api.lemonsqueezy.com/v1/stores", headers=headers, timeout=10.0
            )
            response.raise_for_status()

            return {
                "status": "healthy",
                "response_time_ms": round((time.time() - start) * 1000, 2),
                "details": {
                    "connected": True,
                    "api_available": True,
                    "store_count": len(response.json().get("data", [])),
                },
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": {"connected": False, "api_available": False},
        }


@router.get("/health/version", response_model=Dict[str, str])
async def version_info() -> Dict[str, str]:
    """
    Get application version information.
    """
    return {
        "version": getattr(settings, "VERSION", "1.0.0"),
        "environment": getattr(settings, "ENVIRONMENT", "development"),
        "name": getattr(settings, "PROJECT_NAME", "MangoSEO API"),
    }


@router.get("/health/services", response_model=Dict[str, List[str]])
async def available_services() -> Dict[str, List[str]]:
    """
    Get list of available services (backend only).
    """
    services = ["database", "api"]

    if getattr(settings, "LEMONSQUEEZY_API_KEY", None):
        services.append("lemon_squeezy")

    if getattr(settings, "SERPAPI_KEY", None):
        services.append("serpapi")

    return {"available_services": services}

@router.get("/health/stats", response_model=Dict[str, object])
async def service_stats() -> Dict[str, object]:
    """
    Get basic service statistics.
    """
    try:
        # Efficient DB-level count
        users_response = await supabase_client.fetch_one("users", select="count")
        user_count = getattr(users_response, "count", 0)

        articles_response = await supabase_client.fetch_one("articles", select="count")
        article_count = getattr(articles_response, "count", 0)

        return {
            "users": user_count,
            "articles": article_count,
            "uptime_seconds": time.time() - start_time,
            "timestamp": time.time(),
        }

    except Exception as e:
        return {"error": f"Failed to get stats: {str(e)}", "users": 0, "articles": 0}
