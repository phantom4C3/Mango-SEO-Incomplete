

# onpageseo/app/core/security.py 

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
from .config import get_settings

settings = get_settings()

# Expect "x-api-key" in request headers
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """
    Verify incoming requests have the correct API key.
    Used for service-to-service authentication.
    """
    if not api_key or api_key != settings.supabase_key:  
        # ⚠️ Replace supabase_key with a dedicated SERVICE_API_KEY in .env for more security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True


def get_service_headers() -> dict:
    """
    Helper for making outbound requests to other services.
    Ensures consistent header usage across microservices.
    """
    return {"x-api-key": settings.supabase_key}


async def verify_internal_secret(request: Request):
    secret = request.headers.get("X-Internal-Secret")
    if secret != settings.onpageseo_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret"
        )
    return {"service": "backend"}
