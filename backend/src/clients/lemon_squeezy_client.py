# backend\src\clients\lemon_squeezy_client.py
"""
LemonSqueezy Integration - Service Layer
Contains all logic for processing LemonSqueezy webhook events.
"""

import hmac
import hashlib
import json
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from ..core.config import settings
from ...src.clients.supabase_client import supabase_client
from ..core.exceptions import WebhookError

ALLOWED_EVENTS = {
    "subscription_created",
    "subscription_updated",
    "subscription_cancelled",
    "subscription_expired",
    "subscription_payment_failed",
    "subscription_payment_success",
}


def validate_signature(payload: bytes, signature: str) -> bool:
    """Validate LemonSqueezy webhook signature using HMAC SHA256."""
    try:
        expected_signature = hmac.new(
            settings.lemonsqueezy_webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"LemonSqueezy signature validation failed: {str(e)}")
        return False


async def ensure_profile(user_id: str, email: str = None):
    response = await supabase_client.table("profiles").select("id").eq("id", user_id).maybe_single().execute()
    if not response.data:
        await supabase_client.table("profiles").insert({
            "id": user_id,
            "email": email or "",
            "paid": False,
            "subscription_id": None
        }).execute()
        
async def process_webhook_event(payload_bytes: bytes, signature: str) -> dict:
    """
    Process LemonSqueezy webhook payload.
    Validates signature, parses payload, stores subscription in Supabase.
    """
    # Step 1: Verify webhook signature
    if not validate_signature(payload_bytes, signature):
        raise WebhookError(
            detail="Invalid webhook signature", operation="lemon_squeezy"
        )

    # Step 2: Parse payload
    event = json.loads(payload_bytes)
    event_name = event.get("meta", {}).get("event_name")

    if event_name not in ALLOWED_EVENTS:
        logger.info(f"Ignoring unsupported LemonSqueezy event: {event_name}")
        return {"status": "ignored", "event": event_name}

    custom_data = event.get("meta", {}).get("custom_data", {})
    data = event.get("data", {})
    subscription_id = data.get("id")
    attributes = data.get("attributes", {})

    logger.info(
        f"Processing LemonSqueezy event: {event_name} for subscription {subscription_id}"
    )

    # Step 3: Prepare subscription data (matching latest schema)
    subscription_data = {
        "subscription_id": subscription_id,
        "user_id": custom_data.get("user_id"),
        "plan": attributes.get("product_name") or attributes.get("variant_name"),
        "status": attributes.get("status"),
        "credits": attributes.get("credits") or 0,
        "articles_this_month": attributes.get("articles_this_month") or 0,
        "articles_total": attributes.get("articles_total") or 0,
        "impressions": attributes.get("impressions") or 0,
        "clicks": attributes.get("clicks") or 0,
        "current_period_end": attributes.get("renews_at"),
        "renews_at": attributes.get("renews_at"),
        "updated_at": datetime.utcnow().isoformat(),
        "event_name": event_name,
    }

    # Step 4: Upsert into subscriptions table (user_id is unique)
    response = (
        await supabase_client.table("subscriptions")
        .upsert(subscription_data, on_conflict="user_id")
        .execute()
    )

    if getattr(response, "error", None):
        logger.error(f"Failed to update subscription: {response.error}")
        raise WebhookError(
            detail="Failed to store subscription in Supabase",
            operation="lemon_squeezy",
        )

    return {
        "status": "success",
        "event": event_name,
        "subscription_id": subscription_id,
    }
