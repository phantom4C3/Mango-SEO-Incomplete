# backend\src\api\v1\webhooks\lemonsqueezy.py

"""
LemonSqueezy Webhook Route - Router Layer
Exposes webhook endpoint, delegates processing to integration/service layer.
"""

from fastapi import APIRouter, Request, HTTPException
import logging
from ....clients.lemon_squeezy_client import process_webhook_event

router = APIRouter(prefix="/webhooks/lemon-squeezy", tags=["lemon_squeezy"])

logger = logging.getLogger(__name__)

@router.post("/")
async def lemon_squeezy_webhook(request: Request):
    """
    Endpoint to handle LemonSqueezy subscription webhooks.
    Delegates processing to integrations.api.lemon_squeezy.
    """
    try:
        payload_bytes = await request.body()
        signature = request.headers.get("x-signature", "")

        result = await process_webhook_event(payload_bytes, signature)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error handling LemonSqueezy webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )
