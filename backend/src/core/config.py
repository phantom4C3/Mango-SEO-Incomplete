from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, field_validator
from pathlib import Path
from typing import List, Optional

class Settings(BaseSettings):
    # FastAPI Core
    project_name: str = Field("MangoSEO API", validation_alias="PROJECT_NAME")
    version: str = Field("0.1.0", validation_alias="VERSION")
    debug: bool = Field(False, validation_alias="DEBUG")

    # Server
    host: str = Field("0.0.0.0", validation_alias="HOST")
    port: int = Field(8000, validation_alias="PORT")

    backend_cors_origins: List[AnyHttpUrl] = Field(
    [
        "http://localhost:8000",   # your frontend
        "http://127.0.0.1:8000",
        "http://localhost:3000",   # keep if you ever use Next.js default
    ],
    validation_alias="BACKEND_CORS_ORIGINS"
)


    @field_validator("backend_cors_origins", mode="before")
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Supabase
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., validation_alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(..., validation_alias="SUPABASE_ANON_KEY")

    # External APIs 
    gemini_api_key: Optional[str] = Field(None, validation_alias="GEMINI_API_KEY") 

    # microservices
    ai_blog_writer_url: str = Field(..., validation_alias="AI_BLOG_WRITER_URL")
    onpageseo_url: str = Field(..., validation_alias="ONPAGESEO_URL")

    # Public API
    public_api_url: str = Field("https://api.mangoseo.com/api/v1", validation_alias="PUBLIC_API_URL")

    # CMS
    cms_supported: List[str] = [
        "wordpress", "webflow", "shopify", "ghost", "wix", "framer",
        "hubspot", "notion", "medium", "squarespace", "blogger", "substack"
    ]

    # Languages
    languages_supported: List[str] = [
        "en", "es", "fr", "de", "hi", "zh", "ar", "pt", "ru", "ja", "ko", "it",
        "tr", "nl", "sv", "fi", "no", "da", "pl", "cs", "el", "he", "id", "ms",
        "th", "vi", "bn", "ta", "te", "mr", "gu", "kn", "pa", "ur", "fa", "ro",
        "hu", "uk", "sr", "sk", "sl", "hr", "bg", "lt", "lv", "et", "mt", "is", "cy", "sq", "sw"
    ]

    # Security
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    algo: str = Field(..., validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    ai_blog_writer_secret: str = Field(..., validation_alias="AI_BLOG_WRITER_SECRET")
    onpageseo_secret: str = Field(..., validation_alias="ONPAGESEO_SECRET") 

    # Lemon Squeezy
    lemonsqueezy_api_key: str = Field(..., validation_alias="LEMONSQUEEZY_API_KEY")
    lemonsqueezy_webhook_secret: str = Field(..., validation_alias="LEMONSQUEEZY_WEBHOOK_SECRET")

    # Cloudinary
    cloudinary_cloud_name: str = Field(..., validation_alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(..., validation_alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(..., validation_alias="CLOUDINARY_API_SECRET")

    # Celery
    celery_broker_url: str = Field(..., validation_alias="CELERY_BROKER_URL")
    celery_backend_url: str = Field(..., validation_alias="CELERY_BACKEND_URL")

    # Redis
    redis_url: Optional[str] = Field(None, validation_alias="UPSTASH_REDIS_REST_URL")
    redis_token: Optional[str] = Field(None, validation_alias="UPSTASH_REDIS_REST_TOKEN")

    # Defaults
    default_word_count: int = Field(1000, validation_alias="DEFAULT_WORD_COUNT")
    html_tags_allowed: List[str] = ["p", "h1", "h2", "ul", "ol", "li", "a", "img"]

    # Pydantic v2 config → always load .env from project root
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8"
    )


# Global instance
settings = Settings()



# ⚡ SECRET_KEY generation should not regenerate on every load → better to enforce via .env.
