# backend\src\core\auth.py

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import requests, time, logging
from pydantic import BaseModel
from fastapi import Request
from functools import wraps
from .config import settings

logger = logging.getLogger(__name__)

SUPABASE_PROJECT_REF = "your-project-ref"
SUPABASE_JWKS_URL = f"https://{SUPABASE_PROJECT_REF}.supabase.co/auth/v1/.well-known/jwks.json"
SUPABASE_JWT_AUDIENCE = "authenticated"

bearer_scheme = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str | None = None
    role: str | None = None
    phone: str | None = None

# simple cache for JWKS
JWKS_CACHE_TTL = 3600
_jwks_cache = {"keys": None, "last_updated": 0}

def get_jwks():
    now = time.time()
    if _jwks_cache["keys"] is None or now - _jwks_cache["last_updated"] > JWKS_CACHE_TTL:
        _jwks_cache["keys"] = requests.get(SUPABASE_JWKS_URL).json()
        _jwks_cache["last_updated"] = now
    return _jwks_cache["keys"]

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> User:
    """
    Fetch user once per request and cache in request.state.
    """
    if hasattr(request.state, "current_user"):
        return request.state.current_user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # extract key id
        headers = jwt.get_unverified_header(token)
        jwks = get_jwks()

        rsa_key = next((key for key in jwks["keys"] if key["kid"] == headers["kid"]), None)
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token: no matching key")

        public_key = RSAAlgorithm.from_jwk(rsa_key)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=SUPABASE_JWT_AUDIENCE,
            options={"verify_aud": True, "verify_exp": True},
        )

        user = User(
            id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role"),
            phone=payload.get("phone"),
        )

        # Cache in request.state
        request.state.current_user = user
        return user

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# later add this def require_subscription(min_tier: str):
    # tiers = ["basic", "standard", "premium"]
def require_premium_user(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            raise HTTPException(status_code=500, detail="Request missing in decorator")

        user = getattr(request.state, "current_user", None)
        if not user:
            from .auth import get_current_user
            user = await get_current_user(request)

        if user.role != "premium":  # or use a subscription_type field
            raise HTTPException(status_code=403, detail="Premium subscription required")
        return await func(*args, **kwargs)

    return wrapper



def get_service_headers(service_name: str) -> dict:
    """
    Return headers for internal service communication
    based on the service name.
    """
    secrets = {
        "ai_blog_writer": settings.ai_blog_writer_secret,
        "onpageseo": settings.onpageseo_secret,
    }

    secret = secrets.get(service_name)
    if not secret:
        raise ValueError(f"No secret configured for service: {service_name}")
    return {"X-Internal-Secret": secret}


















# # sample for email inclusion 
# async def get_current_user(
#     request: Request,
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ) -> Dict[str, Any]:
#     # Check if user is already stored in request.state
#     if hasattr(request.state, "current_user"):
#         return request.state.current_user

#     token = credentials.credentials
#     try:
#         payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algo])
#         username = payload.get("sub")
#         if not username:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

#         email = payload.get("email") or payload.get("sub")
#         if not email:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No email in token")

#         user = await supabase_client.fetch_one("users", filters={"email": email})
#         if not user:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

#         # Save in request.state for this request
#         request.state.current_user = user
#         return user

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
