# backend/src/middleware/rate_limiter.py
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID

import logging
from fastapi import HTTPException, Request, status
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)
DISABLE_RATE_LIMIT = True


class RateLimiter:
    """Generic rate limiter for various types of limits."""

    def __init__(self) -> None:
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.limit_config: Dict[str, int] = {
            "api_global": 1000,
            "api_per_user": 100,
            "api_per_ip": 200,
            "ai_global": 500,
            "ai_per_user": 50,
            "openai": 3500,
            "gemini": 60,
            "claude": 100,
            "youtube": 10000,
            "publishing_global": 100,
            "publishing_per_user": 10,
            "db_write": 1000,
            "db_read": 5000,
        }

    def is_rate_limited(self, key: str, limit_type: str, window_seconds: int = 60) -> bool:
        current_time = time.time()
        window_start = current_time - window_seconds
        self.rate_limits[key] = [ts for ts in self.rate_limits[key] if ts > window_start]
        limit = self.limit_config.get(limit_type, 10)
        if len(self.rate_limits[key]) >= limit:
            return True
        self.rate_limits[key].append(current_time)
        return False

    def get_remaining_requests(self, key: str, limit_type: str, window_seconds: int = 60) -> int:
        current_time = time.time()
        window_start = current_time - window_seconds
        self.rate_limits[key] = [ts for ts in self.rate_limits[key] if ts > window_start]
        limit = self.limit_config.get(limit_type, 10)
        return max(0, limit - len(self.rate_limits[key]))

    def get_reset_time(self, key: str, window_seconds: int = 60) -> float:
        if not self.rate_limits[key]:
            return 0.0
        return min(self.rate_limits[key]) + window_seconds


# Global instance
rate_limiter = RateLimiter()


def rate_limit(limit_type: str, key_func: Optional[Callable[..., str]] = None, window_seconds: int = 60) -> Callable:
    """Decorator for function-level rate limiting."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if DISABLE_RATE_LIMIT:
                return await func(*args, **kwargs)

            key = key_func(*args, **kwargs) if key_func else f"{func.__module__}.{func.__name__}"
            if rate_limiter.is_rate_limited(key, limit_type, window_seconds):
                remaining = rate_limiter.get_remaining_requests(key, limit_type, window_seconds)
                reset_time = rate_limiter.get_reset_time(key, window_seconds)
                logger.warning(f"Rate limit exceeded for {limit_type}. Key: {key}, Remaining: {remaining}, Reset in: {reset_time - time.time():.1f}s")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit_type": limit_type,
                        "remaining": remaining,
                        "reset_in": max(0, reset_time - time.time()),
                        "retry_after": max(1, int(reset_time - time.time())),
                    },
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitMiddleware:
    """Async FastAPI middleware for global, per-IP, and per-user rate limits."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if DISABLE_RATE_LIMIT:
            # 🚀 Skip limiting, pass directly to app
            await self.app(scope, receive, send)
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        # Allow OPTIONS requests to pass through without rate limiting
        if request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        client_ip = request.client.host if request.client else "unknown"
        user_id = request.headers.get("x-user-id", "anonymous")

        # Rate limit keys
        global_key = "api_global"
        ip_key = f"api_ip_{client_ip}"
        user_key = f"api_user_{user_id}"

        for key, limit_type in [(global_key, "api_global"), (ip_key, "api_per_ip")]:
            if rate_limiter.is_rate_limited(key, limit_type):
                raise HTTPException(status_code=429, detail=f"{limit_type} limit exceeded")

        if user_id != "anonymous" and rate_limiter.is_rate_limited(user_key, "api_per_user"):
            raise HTTPException(status_code=429, detail="User rate limit exceeded")

        # Call downstream app (no wrapper needed)
        await self.app(scope, receive, send)



class PublishingRateLimiter:
    """Publishing-specific rate limiting."""

    def check_publishing_limit(self, user_id: Union[str, UUID], cms_platform: Optional[str] = None) -> bool:
        user_id_str = str(user_id)
        global_key = "publishing_global"
        user_key = f"publishing_user_{user_id_str}"

        if cms_platform:
            platform_key = f"publishing_{cms_platform}"
            if rate_limiter.is_rate_limited(platform_key, f"publishing_{cms_platform}", 3600):
                return True

        if rate_limiter.is_rate_limited(global_key, "publishing_global", 3600):
            return True

        if rate_limiter.is_rate_limited(user_key, "publishing_per_user", 86400):
            return True

        return False


publishing_rate_limiter = PublishingRateLimiter()


def publishing_rate_limit() -> Callable:
    """Decorator for publishing-specific rate limiting."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if DISABLE_RATE_LIMIT:
                return await func(*args, **kwargs)
            user_id = kwargs.get("user_id") or (args[1] if len(args) > 1 else None)
            cms_platform = kwargs.get("cms_platform")
            if publishing_rate_limiter.check_publishing_limit(user_id, cms_platform):
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Publishing rate limit exceeded")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
