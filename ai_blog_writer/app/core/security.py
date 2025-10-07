# ai_blog_writer/app/core/security.py
import hashlib
import hmac
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from .config import settings
from ..clients.supabase_client import supabase_client
from shared_models.models import LANGUAGES_SUPPORTED
from fastapi import Request, HTTPException, status, Depends 

# -------------------------
# Password hashing (no passlib)
# -------------------------
SECRET_SALT = getattr(settings, "PASSWORD_SALT", "default_salt")

def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA-256 + a static salt.
    (Not as strong as bcrypt, but avoids external deps)
    """
    return hashlib.sha256(f"{SECRET_SALT}{password}".encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password by hashing with the same salt and comparing securely.
    """
    expected_hash = get_password_hash(plain_password)
    return hmac.compare_digest(expected_hash, hashed_password)

# -------------------------
# API Key header
# -------------------------
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

# -------------------------
# User authentication (async)
# -------------------------
async def authenticate_user(username: str, password: str):
    try:
        user_data = await supabase_client.fetch_one(
            table_name="users",
            filters={"username": username}
        )
        if user_data and verify_password(password, user_data.get("password")):
            return user_data
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
    return None

async def create_user(username: str, password: str, email: str):
    try:
        hashed_password = get_password_hash(password)
        inserted = await supabase_client.insert_into(
            table_name="users",
            data={"username": username, "password": hashed_password, "email": email}
        )
        return inserted[0] if inserted else None
    except Exception as e:
        print(f"Failed to create user: {str(e)}")
    return None

# -------------------------
# API Key / Inter-service security
# -------------------------

async def verify_internal_secret(request: Request):
    """Verify secret for inter-service communication (backend → ai_blog_writer)."""
    secret = request.headers.get("X-Internal-Secret")
    if secret != settings.ai_blog_writer_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret"
        )
    return {"service": "backend"}


def verify_inter_service_secret(secret: str) -> bool:
    """Verify inter-service communication secret."""
    return secret == getattr(settings, "INTER_SERVICE_SECRET", None)

def validate_language(lang: str) -> bool:
    """
    Check if the language code is supported by the AI models.
    Returns True if supported, False otherwise.
    """
    return lang.lower() in [l.lower() for l in LANGUAGES_SUPPORTED]

 

async def verify_internal_secret(request: Request):
    """Verify secret for inter-service communication (backend → ai_blog_writer)."""
    secret = request.headers.get("X-Internal-Secret")
    if secret != settings.ai_blog_writer_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret"
        ) 

# -------------------------
# API Key verification
# -------------------------

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify external API requests using X-API-KEY header."""
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return api_key
