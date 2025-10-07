
# backend\src\api\v1\__init__.py
from fastapi import APIRouter

# Import routers from individual endpoint files
from .endpoints import (
    blog_generation,
    blog_topic_generation,
    health,
    publish_cms,
    seo_analysis,
    seo_pixel,
)
from .webhooks import lemonsqueezy

# Create main API router
api_router = APIRouter()

# Blog Generation endpoints
api_router.include_router(blog_generation.router, prefix="/blog-generation", tags=["Blog Generation"])
api_router.include_router(blog_topic_generation.router, prefix="/blog-topics", tags=["Blog Topics"])

# Health endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Publishing endpoints
api_router.include_router(publish_cms.router, prefix="/publish", tags=["Publishing"])

# SEO endpoints
api_router.include_router(seo_analysis.router, prefix="/seo", tags=["SEO Analysis"])
api_router.include_router(seo_pixel.router, prefix="/seo/pixel", tags=["SEO Pixel"])

# Webhooks
api_router.include_router(lemonsqueezy.router, prefix="/webhooks/lemonsqueezy", tags=["Webhooks"])
