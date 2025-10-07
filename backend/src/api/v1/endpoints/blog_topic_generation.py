# backend\src\api\v1\endpoints\blog_topic_generation.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
import uuid
from ....services.blog_generation_service import (
    scrape_website_basic,
    validate_and_normalize_url
)
from typing import List, Dict
from ....clients.supabase_client import supabase_client
from ....services.task_service import task_service
from ....core.auth import get_current_user
from ....core.config import settings
import httpx
import logging
from shared_models.models import TopicRequest
router = APIRouter()
logger = logging.getLogger(__name__)


# auth current user and security current users are not consistent


@router.post("/topics")
async def generate_topics(
    request: TopicRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):

    """
    Main endpoint: Creates task, saves scraped data, triggers background topic generation.
    Returns task ID and optionally fetched topics after generation.
    """
    try:
        
        
                # 0️⃣ Check if topics already exist for this website
        if not request.force_regenerate:
            existing = await supabase_client.fetch_all(
                "topics",
                filters={"website_url": normalized_url, "user_id": user.id}
            )
            if existing:  # already a list
                logger.info(f"Topics already exist for {normalized_url}, skipping AI generation")

                # Optionally update task for tracking
                task_id = await task_service.create_task(
                    user_id=user.id,
                    website_url=normalized_url,
                    website_info=None,
                    task_type="topic_generation",
                    parameters={
                        "user_id": user.id,
                        "website_url": normalized_url,
                        "status": "completed",
                        "progress": "Skipped (already exists)",
                        "task_type": "topic_generation",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                )

                return {
                    "status": "success",
                    "message": "Topics already exist, skipped regeneration",
                    "task_id": task_id,
                    "topics": existing,
                    "skipped_existing": True,
                }


        # 1️⃣ Validate user
        user = current_user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user token")

        # 2️⃣ Validate and normalize URL
        normalized_url = validate_and_normalize_url(request.website_url)

        task_id = await task_service.create_task(
            user_id=user.id,
            website_url=normalized_url,
            website_info=None,  # Optional: you can fill after scraping if needed
            task_type="topic_generation",
            parameters={
                "user_id": user.id,
                "website_url": normalized_url,
                "status": "processing",
                "progress": "Starting topic generation",
                "task_type": "topic_generation",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },  # Add any relevant workflow parameters
        )

        logger.info(f"Created topic generation task {task_id} for user {user.id}")

        # 4️⃣ Trigger background processing
        background_tasks.add_task(
            _process_topic_generation, user.id, normalized_url, task_id
        )

        # 5️⃣ Optional: Fetch topics after generation (for immediate feedback, non-blocking)
        # This could be polled later, but included here for UX enhancement
        topics = await _fetch_generated_topics(task_id, user.id)

        return {
            "status": "processing",
            "message": "Topic generation started",
            "task_id": task_id,
            "topics": (
                topics if topics else None
            ),  # Optional, can be polled via /orchestration-status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start topic generation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate topics: {str(e)}"
        )


async def _process_topic_generation(user_id: str, website_url: str, task_id: str):
    """
    Background task: Scrapes website, saves data, and calls AI Worker for topic generation.
    """

    try:
        # 1. Update task status
        await supabase_client.update_table(
            "tasks",
            filters={"id": str(task_id)},
            updates={
                "status": "processing",
                "progress": "Scraping website content",
                "updated_at": datetime.utcnow().isoformat(),
            },
        )


        # 2. Scrape website (with fallback)
        scrape_status = "success"
        try:
            website_info = await scrape_website_basic(website_url)
        except Exception as scrape_error:
            logger.warning(f"Scraping failed, using fallback: {scrape_error}")
            scrape_status = "fallback"
            website_info = {
                "title": website_url,
                "description": "Website content unavailable",
                "detected_language": "en",
            }

        # 3. Save scraped data to scraped_data table
        scrape_id = str(uuid.uuid4())
        scrape_record = {
            "id": scrape_id,
            "user_id": user_id,
            "website_url": website_url,
            "title": website_info.get("title", "Unknown Title"),
            "description": website_info.get("description", "No description available"),
            "detected_language": website_info.get("detected_language", "en"),
            "status": scrape_status,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await supabase_client.insert_into("scraped_data", scrape_record)
        logger.info(f"Saved scraped data for task {task_id} with ID {scrape_id}")

        # 4. Prepare payload for AI Worker
        payload = {
            "website_info": {
                "title": website_info.get("title", "Unknown Title"),
                "description": website_info.get(
                    "description", "No description available"
                ),
                "user_id": user_id,
                "website_url": website_url,
                "task_id": task_id,
                "scrape_id": scrape_id,  # Optional: Pass scrape_id for traceability
            }
        }

        # 5. Call AI Worker (will save results to DB)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ai_blog_writer_URL}/api/v1/suggest_blog_topics",
                json=payload,
                headers={"X-API-Key": settings.ai_blog_writer_API_KEY},
            )
            response.raise_for_status()

        logger.info(f"Topic generation completed for task {task_id}")

    except Exception as e:
        logger.error(f"Topic generation failed for task {task_id}: {str(e)}")

        # Update task as failed
        try:
            await supabase_client.update_table(
                "tasks",
                filters={"id": str(task_id)},
                updates={
                    "status": f"failed {str(e)}",
                    "progress": "Scraping website content",
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            logger.exception(f"Failed to update task {task_id} status to failed")


async def _fetch_generated_topics(task_id: str, user_id: str) -> List[Dict]:
    """
    Fetch recently generated topics for a given task_id.
    """ 
    topics = await supabase_client.fetch_all(
            "topics",
            filters={"task_id": str(task_id), "user_id": str(user_id)}
        )
    return topics
  
