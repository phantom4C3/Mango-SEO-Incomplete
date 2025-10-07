# backend/src/utils/cms_helpers.py

from typing import Dict, Any, Union
from shared_models.models import (
    CMSCredentials, 
)

def validate_credentials(credentials: CMSCredentials) -> None:
    """Validate CMS credentials based on type."""
    platform = credentials.cms_platform.value

    if platform == "wordpress" and not getattr(credentials, "url", None):
        raise ValueError("WordPress credentials require a 'url'.")
    elif platform == "webflow" and not getattr(credentials, "api_key", None):
        raise ValueError("Webflow credentials require an 'api_key'.")
    elif platform == "shopify" and not getattr(credentials, "access_token", None):
        raise ValueError("Shopify credentials require an 'access_token'.")
    elif platform == "hubspot" and not getattr(credentials, "access_token", None):
        raise ValueError("HubSpot credentials require an 'access_token'.")
    elif platform == "notion" and not getattr(credentials, "api_key", None):
        raise ValueError("Notion credentials require an 'api_key'.")
    elif platform == "wix" and not getattr(credentials, "api_key", None):
        raise ValueError("Wix credentials require an 'api_key'.")
    elif platform == "ghost" and not (
        getattr(credentials, "admin_api_key", None) or getattr(credentials, "content_api_key", None)
    ):
        raise ValueError("Ghost credentials require an 'admin_api_key' or 'content_api_key'.")
    elif platform == "medium" and not getattr(credentials, "access_token", None):
        raise ValueError("Medium credentials require an 'access_token'.")
    elif platform == "blogger" and not getattr(credentials, "blog_id", None):
        raise ValueError("Blogger credentials require a 'blog_id'.")
    elif platform == "substack" and not getattr(credentials, "api_key", None):
        raise ValueError("Substack credentials require an 'api_key'.")
    elif platform == "bits_and_bytes" and not getattr(credentials, "api_key", None):
        raise ValueError("BitsAndBytes credentials require an 'api_key'.")
    elif platform == "custom_rest" and not getattr(credentials, "base_url", None):
        raise ValueError("Custom REST API credentials require a 'base_url'.")

def map_article_to_cms_format(article: Dict[str, Any], cms_type: str) -> Dict[str, Any]:
    """
    Map internal article structure to CMS-specific API payload.
    """
    if cms_type == "wordpress" or cms_type == "ghost":
        return {
            "title": article.get("title", ""),
            "content": article.get("content", ""),
            "status": article.get("status", "publish"),
            "tags": article.get("tags", []),
        }
    elif cms_type == "webflow":
        return {"fields": article}
    elif cms_type == "shopify":
        return {"article": article}
    elif cms_type == "hubspot":
        return article
    elif cms_type == "notion":
        return article
    elif cms_type == "wix":
        return article
    elif cms_type == "framer":
        return article
    elif cms_type == "medium":
        mapped = {
            "title": article.get("title", ""),
            "contentFormat": "html",
            "content": article.get("content", ""),
            "tags": article.get("tags", []),
            "publishStatus": article.get("status", "public"),
        }
        if "publicationId" in article:
            mapped["publicationId"] = article["publicationId"]
        return mapped
    elif cms_type == "blogger":
        return {
            "title": article.get("title", ""),
            "content": article.get("content", ""),
            "labels": article.get("tags", []),
        }
    elif cms_type == "substack":
        return article
    elif cms_type == "bits_and_bytes":
        return article
    elif cms_type == "custom_rest":
        return article
    else:
        raise ValueError(f"Unsupported CMS type: {cms_type}")

def extract_post_id(response: Dict[str, Any], cms_type: str) -> Union[str, None]:
    """
    Extract post ID from CMS response for tracking.
    """
    if cms_type in ["wordpress", "ghost", "webflow", "shopify", "hubspot", "wix", "framer", "substack", "bits_and_bytes"]:
        return str(response.get("id") or response.get("ID"))
    if cms_type == "medium":
        return response.get("data", {}).get("id")
    if cms_type == "blogger":
        return str(response.get("id"))
    if cms_type == "notion":
        return str(response.get("id"))
    if cms_type == "custom_rest":
        return str(response.get("id"))
    return None
