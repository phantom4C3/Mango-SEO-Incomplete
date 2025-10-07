# backend\src\api\v1\endpoints\blog_generation.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from shared_models.models import OrchestrationRequest 
# Import centralized clients & services
from ....clients.supabase_client import supabase_client
from ....core.auth import get_current_user
from ....clients.redis_client import RedisCache
from ....services.task_service import task_service
from ....core.config import settings
from ....services.blog_generation_service import blog_generation_service
from ....services.blog_generation_service import (
    scrape_website_basic,
    validate_and_normalize_url,
    validate_language
)


logger = logging.getLogger(__name__)
router = APIRouter()



# Example: /orchestration-status/{task_id}
@router.get("/orchestration-status/{task_id}")
async def get_orchestration_status(
    task_id: str, current_user: dict = Depends(get_current_user)  # JWT validated
):
    RedisCached_status = await RedisCache.get_task_status(task_id)
    if RedisCached_status:
        return RedisCached_status 
    task_data = await supabase_client.fetch_one("tasks", {"id": task_id})
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data["status"] in ["pending", "processing"]:
        await RedisCache.set_task_status(task_id, task_data)
    return task_data


@router.post("/orchestrate", response_model=OrchestrationRequest)
async def orchestrate_pipeline(
    request: OrchestrationRequest, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)  # JWT validated
):
    try:
        user = current_user  # already validated
        normalized_url = validate_and_normalize_url(request.website_url)

        if not validate_language(request.target_language):
            raise HTTPException(
                status_code=400,
                detail=f"Language '{request.target_language}' is not supported",
            )

        website_info = await scrape_website_basic(normalized_url)

        # Prepare minimal payload for blog generation
        topic_title = request.article_preferences.get("title") if request.article_preferences else "Auto Blog"
        competitors = request.article_preferences.get("competitors", []) if request.article_preferences else []

        task_id = await task_service.create_task(
            user_id=user["id"],
            website_url=normalized_url,
            website_info=website_info,
            task_type="orchestration",
            parameters={
                "target_language": request.target_language,
                "generate_article": request.generate_article,
                "run_seo_audit": request.run_seo_audit,
                "topic": topic_title,
                "competitors": competitors,
                "original_url": request.website_url,
            },
        )

        # Run orchestration pipeline in background
        background_tasks.add_task(
            _run_orchestration_pipeline,
            user_id=user["id"],
            website_url=normalized_url,
            target_language=request.target_language,
            generate_article=request.generate_article,
            run_seo_audit=request.run_seo_audit,
            article_preferences={"topic": topic_title, "competitors": competitors},
            task_id=task_id,
            website_info=website_info,
        )

        return {"task_id": task_id, "message": "Orchestration pipeline started successfully."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Orchestration pipeline failed to start: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


async def _run_orchestration_pipeline(
    user_id: str,
    website_url: str,
    target_language: str,
    generate_article: bool,
    run_seo_audit: bool,
    article_preferences: Optional[dict],
    task_id: str,
    website_info: Dict[str, Any],
    topic_id: Optional[str] = None,
):
    supabase = supabase_client
    try: 
        await supabase_client.update_table(
            "tasks",
            {"id": task_id},
            {
                "status": "processing",
                "progress": "Starting orchestration pipeline",
                "updated_at": datetime.utcnow().isoformat(),
            }
        )


        # 2️⃣ Prepare minimal payload for AI Blog Writer microservice
        topic_title = article_preferences.get("title") if article_preferences else "Auto Blog"
        competitors = article_preferences.get("competitors", []) if article_preferences else []

        payload = {
            "task_id": task_id,
            "user_id": user_id,
            "topic": topic_title,
            "website_url": website_url,
            "language": target_language,
            "competitors": competitors,
        }

        # 3️⃣ Call blog_generation_service which internally calls /generate
        await blog_generation_service.execute_pipeline(payload)

        await supabase_client.update_table(
            "tasks",
            {"id": task_id},
            {
                "status": "completed",
                "progress": "Orchestration pipeline completed successfully",
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Orchestration pipeline failed for task {task_id}: {str(e)}")
        await supabase_client.update_table(
            "tasks",
            {"id": task_id},
            {
                "status": "failed",
                "progress": f"Failed: {str(e)}",
                "updated_at": datetime.utcnow().isoformat(),
            }
        )



# --- Cancel Orchestration ---
@router.post("/cancel-orchestration/{task_id}")
async def cancel_orchestration(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)  # <- add this
):

    """
    Cancel an ongoing orchestration task and terminate background processes.
    """
    supabase = supabase_client

    try:
        task = await supabase_client.fetch_one("tasks", {"id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")


        # Check if task can be cancelled
        if task["status"] not in ["pending", "processing"]:
            raise HTTPException(
                status_code=400,
                detail=f"Task cannot be cancelled in current state: {task['status']}",
            )

        await supabase_client.update_table(
            "tasks",
            {"id": task_id},
            {
                "status": "cancelling",
                "progress": "Initiating cancellation...",
                "updated_at": datetime.utcnow().isoformat(),
            }
        )


        # Get pipeline ID if available
        task_id = task.get("parameters", {}).get("task_id")

        # Start background task to handle actual termination
        background_tasks.add_task(
            _handle_task_cancellation,
            task_id,
            task_id,
            task.get("task_type"),
            task.get("user_id"),
        )

        return {
            "message": "Cancellation initiated",
            "task_id": task_id,
            "status": "cancelling",
        }

    except Exception as e:
        logger.error(f"Failed to initiate cancellation for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")



async def _handle_task_cancellation(task_id: str, pipeline_id: str, task_type: str, user_id: str):
    """
    Terminate an ongoing orchestration task.
    Implementation depends on how tasks are executed.
    Example: signal microservice, remove from Redis queue, update DB status.
    """
    try:
        # Example: update task status to cancelled
        await supabase_client.update_table(
            "tasks", 
            {"id": task_id},
            {
                "status": "cancelled",
                "progress": "Task cancelled by user",
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        # Optional: signal microservice to stop
        # await blog_generation_service.cancel_task(pipeline_id)
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
