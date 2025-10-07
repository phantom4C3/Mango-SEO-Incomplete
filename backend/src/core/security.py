# backend/src/core/security.py

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi.security import HTTPBearer

from passlib.context import CryptContext
import jwt

from .config import settings
# do NOT import supabase_client at top-level to avoid circular import


 


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
 
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# -------------------------------
# JWT utilities
# -------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algo)


 
