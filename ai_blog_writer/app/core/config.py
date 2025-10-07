# ai_blog_writer/app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
import os 

# --- Path to .env file (ai_blog_writer root) ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

print(f"🔍 Looking for .env at: {ENV_PATH}")
print(f"🔍 File exists: {ENV_PATH.exists()}")

if ENV_PATH.exists():
    print("✅ Using .env file for configuration")
else:
    print("⚠️  .env file not found. Using system environment variables.")

class Settings(BaseSettings):
    # App
    host: str = Field("0.0.0.0", validation_alias="HOST")
    port: int = Field(8001, validation_alias="PORT")
    debug: bool = Field(True, validation_alias="DEBUG")
    cors_origins: Optional[str] = Field(default_factory=lambda: ["*"], validation_alias="CORS_ORIGINS")

    # Backend
    main_backend_url: Optional[str] = Field(None, validation_alias="MAIN_BACKEND_URL")

    # Supabase
    supabase_url: Optional[str] = Field(None, validation_alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(None, validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(None, validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    # AI
    gemini_api_key: Optional[str] = Field(None, validation_alias="GEMINI_API_KEY")
    gemini_nano_api_key: Optional[str] = Field(None, validation_alias="GEMINI_NANO_API_KEY")
    serpapi_key: Optional[str] = Field(None, validation_alias="SERPAPI_KEY")
    youtube_api_key: Optional[str] = Field(None, validation_alias="YOUTUBE_API_KEY")

    # Redis
    redis_url: Optional[str] = Field(None, validation_alias="UPSTASH_REDIS_REST_URL")
    redis_token: Optional[str] = Field(None, validation_alias="UPSTASH_REDIS_REST_TOKEN")

    # Cloudinary
    cloudinary_cloud_name: Optional[str] = Field(None, validation_alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: Optional[str] = Field(None, validation_alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: Optional[str] = Field(None, validation_alias="CLOUDINARY_API_SECRET")

    # Inter-service secrets
    ai_blog_writer_secret: str = Field(..., validation_alias="AI_BLOG_WRITER_SECRET")

    # Optional: if you want multiple allowed API keys
    api_keys: List[str] = Field(default_factory=list, validation_alias="API_KEYS")

    # Pydantic V2 config
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore"
    )

def get_settings() -> Settings:
    """Return settings instance with dotenv support."""
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        print("✅ Manually loaded .env file with dotenv")

    settings = Settings()

    # Debug
    print(f"🛠️  Loaded GEMINI_API_KEY: '{settings.gemini_api_key}'")
    print(f"🛠️  Loaded SUPABASE_URL: '{settings.supabase_url}'")
    print(f"🛠️  OS GEMINI_API_KEY: '{os.getenv('GEMINI_API_KEY')}'")

    return settings

settings = get_settings()
