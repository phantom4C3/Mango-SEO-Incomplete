# backend/src/utils/webhook_helpers.py
from typing import Dict, Optional
import hmac
import hashlib
import json
from datetime import datetime
import asyncio
import logging

from ..clients.supabase_client import supabase_client
from ..core.exceptions import WebhookError
from ..core.config import settings
from ..clients.celery_client import app   

logger = logging.getLogger(__name__)

class WebhookHelpers:
    """Utility class for webhook-related operations using Celery."""

    def __init__(self):
        self.supabase_client = supabase_client

    def validate_lemon_squeezy_signature(self, payload: bytes, signature: str) -> bool:
        """Validate Lemon Squeezy webhook signature."""
        try:
            expected_signature = hmac.new(
                settings.LEMON_SQUEEZY_SIGNING_SECRET.encode("utf-8"),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error validating Lemon Squeezy signature: {str(e)}")
            raise WebhookError(
                detail=f"Signature validation failed: {str(e)}",
                operation="validate_lemon_squeezy_signature"
            )

    async def parse_webhook_payload(self, payload: bytes, provider: str) -> Dict[str, str]:
        """Parse webhook payload and store in Supabase."""
        try:
            payload_dict = json.loads(payload)
            webhook_data = {
                "provider": provider,
                "payload": payload_dict,
                "created_at": datetime.utcnow().isoformat()
            }
            response = await self.supabase_client.table("webhook_events").insert(webhook_data).execute()
            if not response.data:
                raise WebhookError(detail="Failed to store webhook event", operation="parse_webhook_payload")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error parsing webhook payload: {str(e)}")
            raise WebhookError(detail=str(e), operation="parse_webhook_payload")

    def queue_webhook_task(self, task_name: str, payload: Dict[str, str], user_id: str) -> str:
        """Queue a webhook task using Celery."""
        try:
            job = send_webhook_task.delay(task_name, payload, user_id)
            return job.id
        except Exception as e:
            logger.error(f"Error queuing webhook task: {str(e)}")
            raise WebhookError(detail=str(e), operation="queue_webhook_task")

    async def process_subscription_webhook(self, payload: Dict[str, str], provider: str, user_id: str) -> Dict[str, str]:
        """Process subscription webhook and queue tasks for Celery worker."""
        try:
            if provider == "lemon_squeezy":
                event_type = payload.get("meta", {}).get("event_name")
                subscription_id = payload.get("data", {}).get("id")
                status = payload.get("data", {}).get("attributes", {}).get("status")
            elif provider == "stripe":
                event_type = payload.get("type")
                subscription_id = payload.get("data", {}).get("object", {}).get("id")
                status = payload.get("data", {}).get("object", {}).get("status")
            else:
                raise WebhookError(detail="Unsupported provider", operation="process_subscription_webhook")

            subscription_data = {
                "subscription_id": subscription_id,
                "provider": provider,
                "status": status,
                "user_id": user_id,
                "updated_at": datetime.utcnow().isoformat()
            }
            response = await self.supabase_client.table("subscriptions").upsert(subscription_data).execute()
            if not response.data:
                raise WebhookError(detail="Failed to update subscription", operation="process_subscription_webhook")

            # Queue feature enablement task if subscription created
            if event_type in ["subscription_created", "customer.subscription.created"]:
                self.queue_webhook_task(
                    f"{provider}_subscription_enable",
                    {"action": "enable_features", "user_id": user_id},
                    user_id
                )

            # Queue update notification task
            self.queue_webhook_task(f"{provider}_subscription_update", subscription_data, user_id)
            return response.data[0]

        except Exception as e:
            logger.error(f"Error processing subscription webhook: {str(e)}")
            raise WebhookError(detail=str(e), operation="process_subscription_webhook")

    async def log_webhook_event(self, event_type: str, payload: Dict[str, str], user_id: Optional[str] = None) -> Dict[str, str]:
        """Log webhook event for debugging and compliance."""
        try:
            log_data = {
                "event_type": event_type,
                "payload": payload,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat()
            }
            response = await self.supabase_client.table("webhook_logs").insert(log_data).execute()
            if not response.data:
                raise WebhookError(detail="Failed to log webhook event", operation="log_webhook_event")
            return response.data[0]
        except Exception as e:
            logger.error(f"Error logging webhook event: {str(e)}")
            raise WebhookError(detail=str(e), operation="log_webhook_event")


# ----------------------
# Celery Task Definition
# ----------------------
@app.task(bind=True, name="send_webhook_task")
def send_webhook_task(self, task_name: str, payload: Dict[str, str], user_id: str):
    """
    Generic Celery task to process webhook tasks asynchronously.
    This replaces RQ queue.
    """
    logger.info(f"Processing webhook task: {task_name} for user {user_id}")
    # Here you would call the actual worker logic, e.g., enable features, send notifications
    # Example:
    # if task_name.endswith("_enable"):
    #     enable_user_features(user_id)
    # elif task_name.endswith("_update"):
    #     notify_subscription_update(user_id, payload)
    return {"task_name": task_name, "user_id": user_id, "status": "completed"}


# Singleton instance
webhook_helpers = WebhookHelpers()
