# onpageseo-service/app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, AnyHttpUrl
from functools import lru_cache
from typing import Optional
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
import json
from dotenv import load_dotenv

# --- SIMPLE FIX: Define the ABSOLUTE path to the .env file ---
# The .env is in the 'onpageseo-service' directory
BASE_DIR = (
    Path(__file__).resolve().parent.parent.parent
)  # Goes up to 'onpageseo-service'
ENV_PATH = BASE_DIR / ".env"

print(f"🔍 Looking for .env at: {ENV_PATH}")  # Debug print
print(f"🔍 File exists: {ENV_PATH.exists()}")  # Debug print

if ENV_PATH.exists():
    print("✅ Using .env file for configuration")
    # DEBUG: Let's see what's actually in the file
    with open(ENV_PATH, "r") as f:
        content = f.read()
        print(f"🔍 .env file content:\n{content}")
else:
    print("⚠️  .env file not found. Using system environment variables.")


class Settings(BaseSettings):
    # App
    app_name: Optional[str] = "onpageseo-service"
    environment: Optional[str] = "development"
    gemini_api_key: Optional[str] = Field(None, validation_alias="GEMINI_API_KEY")
    next_public_app_url: Optional[str] = Field(
        None, validation_alias="NEXT_PUBLIC_APP_URL"
    )

    # Supabase
    supabase_url: Optional[str] = Field(None, validation_alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(
        None, validation_alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # Backend
    backend_host: Optional[str] = Field(None, validation_alias="BACKEND_HOST")
    backend_port: int = Field(8000, validation_alias="BACKEND_PORT")
    backend_cors_origins: List[AnyHttpUrl] = Field(
    [
        "http://localhost:8000",   # your frontend
        "http://127.0.0.1:8000",
        "http://localhost:3000",   # keep if you ever use Next.js default
    ],
    validation_alias="BACKEND_CORS_ORIGINS"
)


    # AI / APIs
    openai_api_key: Optional[str] = Field(None, validation_alias="OPENAI_API_KEY")
    serpapi_key: Optional[str] = Field(None, validation_alias="SERPAPI_KEY")
    ahrefs_key: Optional[str] = Field(None, validation_alias="AHREFS_KEY")
    anthropic_api_key: Optional[str] = Field(None, validation_alias="ANTHROPIC_API_KEY")
    mistral_api_key: Optional[str] = Field(None, validation_alias="MISTRAL_API_KEY")
    pagespeed_api_key: Optional[str] = Field(None, validation_alias="PAGESPEED_API_KEY")
    ga4_property_id: Optional[str] = Field(None, validation_alias="GA4_PROPERTY_ID")

    # Google Service Account - FIXED: Added proper typing imports
    google_service_account_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Google Service Account JSON as dict",
        validation_alias="GOOGLE_SERVICE_ACCOUNT_JSON",
    )

    # Redis
    redis_url: Optional[str] = Field(validation_alias="UPSTASH_REDIS_REST_URL")
    redis_token: Optional[str] = Field(
        None, validation_alias="UPSTASH_REDIS_REST_TOKEN"
    )

    
    # Inter-service secrets
    onpageseo_secret: str = Field(..., validation_alias="ONPAGESEO_SECRET")

    # Optional: dedicated API key instead of using Supabase anon key
    service_api_key: Optional[str] = Field(None, validation_alias="ONPAGESEO_API_KEY")

    # AI Worker
    ai_blog_writer_url: Optional[str] = Field(
        "http://ai-worker:8000", validation_alias="ai_blog_writer_URL"
    )

    # Crawler
    crawler_user_agent: Optional[str] = Field(
        None, validation_alias="CRAWLER_USER_AGENT"
    )
    request_timeout: int = Field(30, validation_alias="REQUEST_TIMEOUT")
    max_retries: int = Field(3, validation_alias="MAX_RETRIES")

    # Validator for JSON parsing
    @field_validator("google_service_account_json")
    def parse_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string in GOOGLE_SERVICE_ACCOUNT_JSON")
        return v

    
# Pydantic v2 config → always load .env from project root
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8"
    )

# @lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance and log critical values."""
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        print("✅ Manually loaded .env file with dotenv")

    settings = Settings()

    # Debug checks
    print(f"🛠️  Loaded GEMINI_API_KEY: '{settings.gemini_api_key}'")
    print(f"🛠️  Loaded SUPABASE_URL: '{settings.supabase_url}'")
    print(f"🛠️  OS GEMINI_API_KEY: '{os.getenv('GEMINI_API_KEY')}'")

    return settings

settings = Settings()
