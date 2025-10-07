# onpageseo/app/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..clients.redis_client import redis_client
import logging
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
DISABLE_RATE_LIMIT = True

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 30, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window

    async def dispatch(self, request: Request, call_next):
        if DISABLE_RATE_LIMIT:
            return await call_next(request)
        # keep rest of your logic intact

        print(f"[Middleware] Method={request.method}, Path={request.url.path}")  # ✅ add this
        if request.method == "OPTIONS":
            # Return 200 directly for preflight; CORSMiddleware will add headers
            from fastapi.responses import Response
            return Response(status_code=200)

        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path

        # Use a key only for user-triggered requests
        key = f"rate:{client_ip}:{endpoint}"

        # Increment counter once per true request
        count = await redis_client.increment_with_expiry(key, ttl=self.window)

        if count is None:
            logger.warning(f"RateLimiter: Redis unavailable for key {key}")
            return await call_next(request)

        logger.info(f"RateLimiter count for {key}: {count}")

        if count > self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: {self.max_requests} requests "
                    f"in {self.window}s window. Current count={count}"
                ),
            )

        return await call_next(request)
    
