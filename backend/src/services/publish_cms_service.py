import logging
from uuid import UUID
from typing import Dict, Any
from datetime import datetime
import asyncio

from ..clients.supabase_client import supabase_client
from shared_models.models import CMSCredentials
from ..core.exceptions import IntegrationError
from ..utils.content_helper import content_helper
from ..integrations.base_cms_client import BaseCMSClient
from .crosslinking_service import cross_linking_service

logger = logging.getLogger(__name__)
 
class PublishCMSService:
    """Service dedicated ONLY to CMS publishing"""

async def publish_article(self, article_id: UUID, user_id: UUID, task_id: str) -> Dict[str, Any]:
    
    from ..tasks import crosslink_blogs_task   # ⬅️ add import at top
    
    now = datetime.utcnow().isoformat()  # single timestamp for consistency
    try:
        # Fetch article from DB
        article_record = await supabase_client.fetch_one("blog_results", {"id": str(article_id)})
        if not article_record:
            raise IntegrationError(detail="Article not found", operation="publish_article")

        # Mark as processing
        await supabase_client.update_table(
            "blog_results",
            {"id": str(article_id)},
            {"status": "processing", "updated_at": now}
        )

        # Format content for CMS
        cms_ready_html = await content_helper.format_for_cms(article_record, str(user_id))

        # Fetch CMS credentials (support multiple CMS for the user)
        creds_records = await supabase_client.fetch_all("cms_credentials", {"user_id": str(user_id)})
        if not creds_records:
            raise IntegrationError(detail="No CMS credentials found", operation="publish_article")

        # Prepare article payload
        article_data = {
            "title": article_record["title"],
            "slug": article_record["slug"],
            "content": cms_ready_html,
            "featured_image_url": article_record.get("featured_image_url"),
            "meta_description": article_record.get("meta_description"),
        }

        # Create CMS clients concurrently
        cms_clients = await asyncio.gather(*[
            BaseCMSClient.create_cms_client(CMSCredentials.parse_obj(creds)) for creds in creds_records
        ])

        # Publish to all CMS platforms in parallel
        publish_tasks = [client.publish_article(article_data) for client in cms_clients]
        results = await asyncio.gather(*publish_tasks, return_exceptions=True)

        cms_publish_info = {}

        for res, client in zip(results, cms_clients):
            platform = client.cms_type
            if isinstance(res, Exception):
                cms_publish_info[platform] = {
                    "status": "failed",
                    "error_message": str(res)
                }
                logger.exception(f"Publishing failed on {platform}")
            else:
                cms_publish_info[platform] = {
                    "status": "completed",
                    "cms_id": res.get("id") or res.get("cms_id"),
                    "post_url": res.get("url") or res.get("permalink")
                }

        # Update CMS publish info in DB
        await supabase_client.update_table(
            "blog_results",
            {"id": str(article_id)},
            {"cms_publish_info": cms_publish_info, "updated_at": now}
        )

        # Perform initial internal linking
        await cross_linking_service.initial_link_and_update(str(article_id))

        # Determine overall status
        overall_status = "completed" if all(info["status"] == "completed" for info in cms_publish_info.values()) else "partial_failed"

        await supabase_client.update_table(
            "blog_results",
            {"id": str(article_id)},
            {"status": overall_status, "updated_at": now}
        )

        # Queue comprehensive crosslinking asynchronously
        try:
            crosslink_blogs_task.delay(str(article_id))
            logger.info(f"Queued comprehensive crosslinking for article {article_id}")
        except Exception as ce:
            logger.error(f"Failed to queue crosslinking task for article {article_id}: {ce}")

    except Exception as e:
        logger.exception(f"Publishing failed for article {article_id}")
        await supabase_client.update_table(
            "blog_results",
            {"id": str(article_id)},
            {"status": "failed", "error_message": str(e), "updated_at": now}
        )
        raise IntegrationError(detail=str(e), operation="publish_article")




publish_cms_service = PublishCMSService()



