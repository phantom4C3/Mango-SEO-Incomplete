# ai_blog_writer/src/middleware/redis_rate_limiter.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from functools import wraps 
from typing import Callable, Optional

from ..clients.redis_client import redis_client


class RedisRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed rate limiter middleware for HTTP requests.
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip harmless requests
        if request.method in ("OPTIONS", "HEAD"):
            return await call_next(request)

        client_ip = request.client.host
        user_id = request.headers.get("x-user-id", "anonymous")
        endpoint = request.url.path

        # Redis key: per IP and endpoint, optionally per user
        key = f"rate:{client_ip}:{endpoint}:{user_id}"

        # Increment request count with TTL
        count = await redis_client.increment_with_expiry(key, ttl=self.window_seconds)
        if count is None:
            # Redis unavailable, allow request (fail-open)
            print(f"⚠️ Redis unavailable for key {key}")
            return await call_next(request)

        if count > self.max_requests:
            reset_time = await redis_client.get_ttl(key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "max_requests": self.max_requests,
                    "current_count": count,
                    "retry_after_seconds": max(1, reset_time),
                },
            )

        response = await call_next(request)

        # Add rate-limit headers
        reset_time = await redis_client.get_ttl(key)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - count)
        )
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        return response


# Decorator for AI provider limits
def ai_rate_limit(
    provider: str,
    max_requests: int,
    window_seconds: int = 60,
    user_key_func: Optional[Callable] = None,
):
    """
    Decorator for Redis-backed AI provider rate limiting.

    Args:
        provider: e.g., "gemini", "openai"
        max_requests: max calls allowed
        window_seconds: time window in seconds
        user_key_func: optional callable to generate per-user key
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = None
            if user_key_func:
                user_id = user_key_func(*args, **kwargs)
            elif "user_id" in kwargs:
                user_id = kwargs["user_id"]

            key = f"ai:{provider}:{user_id or 'global'}"
            count = await redis_client.increment_with_expiry(key, ttl=window_seconds)
            if count is None:
                print(f"⚠️ Redis unavailable for AI rate key {key}")
            elif count > max_requests:
                reset_time = await redis_client.get_ttl(key)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": f"{provider.upper()} rate limit exceeded",
                        "max_requests": max_requests,
                        "current_count": count,
                        "retry_after_seconds": max(1, reset_time),
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
