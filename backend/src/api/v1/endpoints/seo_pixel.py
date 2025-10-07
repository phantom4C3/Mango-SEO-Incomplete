# backend/src/api/endpoints/seo_pixel.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging
from ....core.auth import get_current_user, User, require_premium_user
from fastapi import Request

from ....services.pixel_service import pixel_service
from shared_models.models import (
    PixelGenerationRequest, 
    PixelResponse, 
    PixelRollbackRequest,
    PixelStatusResponse
) 
from ....clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/seo/pixel/generate", response_model=PixelResponse)
async def generate_seo_pixel(
    request: PixelGenerationRequest,
    current_user: User = Depends(get_current_user)  # ✅ Add this
):

    """
    Generate a unique SEO pixel for a website
    """
    try:
        pixel_data = await pixel_service.generate_pixel_code(
            request.website_id, 
            request.user_id,
            request.options
        )
        
        # Store pixel configuration in database
        pixel_config = {
            "id": pixel_data["pixel_id"],
            "website_id": str(request.website_id),
            "user_id": str(request.user_id),
            "options": request.options or {},
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        supabase_client.table("seo_pixels").insert(pixel_config).execute()
        
        return PixelResponse(
            pixel_id=pixel_data["pixel_id"],
            script_code=pixel_data["script_code"],
            installation_instructions=pixel_data["instructions"]
        )
        
    except Exception as e:
        logger.error(f"Failed to generate pixel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate pixel: {str(e)}")

@router.get("/seo/pixel/deploy")
async def get_pixel_deployment(
    pixel_id: str,
    url: str,
    current_user: User = Depends(get_current_user)
)-> Dict[str, Any]:
    """
    Return active SEO payload for a specific page (used by pixel.js)
    """
    try:
        optimizations = await pixel_service.get_optimizations(pixel_id, url)
        
        if not optimizations:
            return {"optimizations": {}}
        
        return {
            "success": True,
            "optimizations": optimizations,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get deployment data: {str(e)}")
        return {"success": False, "optimizations": {}, "error": str(e)}

@router.post("/seo/pixel/rollback")
@require_premium_user
async def rollback_pixel_deployment(
    request: PixelRollbackRequest,
    current_user: User = Depends(get_current_user)
):

    """
    Rollback to a previous version of SEO optimizations
    """
    try:
        success = await pixel_service.rollback_optimizations(
            request.website_id,
            request.url,
            request.version_id
        )
        
        if success:
            return {"success": True, "message": "Rollback completed successfully"}
        else:
            return {"success": False, "message": "Rollback failed"}
            
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

@router.get("/seo/pixel/{pixel_id}/status", response_model=PixelStatusResponse)
@require_premium_user
async def get_pixel_status(
    pixel_id: str,
    current_user: User = Depends(get_current_user)
):

    """
    Get installation status and analytics for a pixel
    """
    try:
        status = await pixel_service.get_pixel_status(pixel_id)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get pixel status: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Pixel not found: {str(e)}")


@router.get("/seo/pixel/{pixel_id}.js", response_class=PlainTextResponse)
async def serve_pixel_script(
    pixel_id: str,  
):
    """
    Serve the pixel JavaScript loader for embedding in websites.
    Example usage in HTML:
    <script src="https://yourdomain.com/api/v1/seo/pixel/{pixel_id}.js"></script>
    """
    try:
        script = await pixel_service.generate_pixel_script(pixel_id)
        return PlainTextResponse(content=script, media_type="application/javascript")
    except Exception as e:
        logger.error(f"Failed to serve pixel script for site {pixel_id}: {str(e)}")
        return PlainTextResponse(
            content=f"// Pixel load failed: {str(e)}",
            media_type="application/javascript",
            status_code=500,
        )
        
        
        
        
        
# Suggested flow:

# User sees recommendations in a UI:

# List all suggested recommendations per page.

# Allow user to approve or reject each one.

# Persist the approved recommendations:

# Store the final approved set in a database table, e.g., approved_ai_recommendations.

# Only mark these as is_active_for_pixel = True (or similar).

# Pixel fetch logic:

# Modify get_active_optimizations to filter only approved recommendations.

# Example filter in Supabase:


