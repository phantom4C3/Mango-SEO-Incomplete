# backend/src/api/v1/endpoints/publish_cms.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from uuid import UUID
from datetime import datetime
import logging

from ....services.publish_cms_service import PublishCMSService
from ....core.exceptions import IntegrationError
from ....services.task_service import TaskService
from ....core.auth import get_current_user, User

router = APIRouter(prefix="/publish", tags=["CMS"])
logger = logging.getLogger(__name__)


def get_publishing_service() -> PublishCMSService:
    return PublishCMSService()



@router.post("/article/{article_id}")
async def publish_article(
    article_id: UUID,
    background_tasks: BackgroundTasks,
    publishing_service: PublishCMSService = Depends(get_publishing_service),
    current_user: User = Depends(get_current_user),  # ✅ JWT auth enforced automatically
):

    """
    Start publishing a generated article to CMS.
    Creates a task, runs publishing in the background.
    """
    try:
        user_id = current_user.id 
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")

        # 2️⃣ Create publishing task
        task_id = await TaskService.create_task(
            user_id=user_id,
            website_url=None,
            task_type="publish_cms",
            parameters={
                "article_id": str(article_id),
                "status": "processing",
                "progress": "Starting CMS publishing",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        )
        
        
        logger.info(f"Publishing task {task_id} created for user {user_id}")

        # 3️⃣ Run publishing service in background
        # Add article_id to the background task; job_id removed
        background_tasks.add_task(
            run_publishing_job, publishing_service, article_id, current_user.id, task_id
        )

        return {
            "status": "processing",
            "message": "Publishing started",
            "task_id": task_id,
        }

    except Exception as e:
        logger.error(f"Failed to start publishing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to publish: {str(e)}")


async def run_publishing_job(
    publishing_service: PublishCMSService, article_id: UUID, user_id: UUID, task_id: str
):
    """
    Background job: wrap PublishCMSService with task status updates.
    """
    try:
        await TaskService.update_task_status(task_id, "processing", "Publishing to CMS")

        # Call the actual service (business logic)
        # Mark publishing as processing
        await publishing_service.update_blog_publish_status(article_id, status="processing")

        # Call the actual service (business logic)
        result = await publishing_service.publish_article(article_id, user_id, task_id)

        # Mark publishing as completed
        await publishing_service.update_blog_publish_status(article_id, status="completed")


        await TaskService.update_task_status(task_id, "completed", "Publishing finished")

        logger.info(f"Publishing task {task_id} completed")
        return result

    except IntegrationError as e:
        await publishing_service.update_blog_publish_status(article_id, status="failed")
        await TaskService.update_task_status(task_id, "failed", f"Integration error: {e}")
        logger.error(f"Publishing failed (IntegrationError): {e}")
    except Exception as e:
        await publishing_service.update_blog_publish_status(article_id, status="failed")
        await TaskService.update_task_status(task_id, "failed", f"Unexpected error: {e}")
        logger.exception(f"Publishing task {task_id} failed")



@router.get("/publishing-status/{task_id}")
async def get_publishing_status(
    task_id: str, current_user: User = Depends(get_current_user)
):
    task = await TaskService.get_task(task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Publishing task not found")
    return task




# You already have a scheduler service for blog posting (scheduler_service.py) — so you can reuse that.
# Initial linking:
# Trigger immediately after blog publish.
# No separate schedule needed. It’s a one-time operation per article.
# Comprehensive relinking:
# Schedule periodically, e.g., once per week for all published articles.
# Could be a separate scheduled task like crosslink_relinking_weekly.