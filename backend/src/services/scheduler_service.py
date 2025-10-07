we# backend/src/services/scheduler_service.py
"""
Centralized scheduler service using Celery.
Handles only scheduling, status checking, and cancellation for:
- CMS publishing
- Publishing SEO recommendations
- Relinking blogs after crosslinking
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from celery.result import AsyncResult
from ..tasks import (
    publish_to_cms_task,
    publish_seo_recs_task,
    crosslink_blogs_task,
)
from ..clients.supabase_client import supabase_client
from ..clients.celery_client import app 
from dateutil.parser import parse as parse_dt
 

def get_schedule_params(prefs: dict, pref_key_freq: str, pref_key_dt: str, default_interval_sec: int):
    """
    Return either a countdown (seconds) or exact datetime (eta) for Celery.
    """
    dt_str = prefs.get(pref_key_dt)
    if dt_str:
        try:
            return {"eta": parse_dt(dt_str)}
        except Exception as e:
            logger.warning(f"Invalid datetime {dt_str}, using default interval: {e}")

    freq = prefs.get(pref_key_freq, "weekly")
    interval_sec = 7*24*3600 if freq == "weekly" else 30*24*3600 if freq == "monthly" else 24*3600
    return {"countdown": interval_sec}


logger = logging.getLogger(__name__)

# -----------------------
# Task Type → Celery Task Mapping
# -----------------------
TASK_MAP = {
    "cms_publishing": publish_to_cms_task,
    "publish_seo_recs": publish_seo_recs_task,
    "crosslink_blogs": crosslink_blogs_task,
}


def get_celery_task(task_type: str):
    """Return the Celery task function for a given task type."""
    return TASK_MAP.get(task_type)

async def get_active_user_ids() -> list[str]:
    """Fetch IDs of all users who need periodic tasks."""
    users = await supabase_client.fetch_all("users", {"active": True})
    return [user["id"] for user in users]

class SchedulerService:
    """Service for submitting and monitoring Celery jobs."""

    async def schedule_task(
        self, task_type: str, args: list, countdown: Optional[int] = None, eta: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Schedule a Celery task based on task_type."""
        celery_task = get_celery_task(task_type)
        if not celery_task:
            logger.warning(f"No Celery handler for task_type={task_type}")
            return None

        if eta:
            result = celery_task.apply_async(args=args, eta=eta)
        elif countdown:
            result = celery_task.apply_async(args=args, countdown=countdown)
        else:
            result = celery_task.delay(*args)

        logger.info(f"Scheduled {task_type} with Celery ID {result.id}")

        return {
            "celery_task_id": result.id,
            "scheduled_at": datetime.utcnow().isoformat(),
        }

    async def retry_task(
        self, task_type: str, args: list, countdown: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Retry a task by re-scheduling it."""
        logger.info(f"Retrying {task_type} with args={args}")
        return await self.schedule_task(task_type, args, countdown)

    async def get_task_status(self, celery_task_id: str) -> Dict[str, Any]:
        """Get status of a Celery task."""
        result = AsyncResult(celery_task_id, app=app)
        return {
            "celery_task_id": celery_task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "date_done": result.date_done.isoformat() if result.date_done else None,
        }

    async def cancel_scheduled_task(self, celery_task_id: str) -> bool:
        """Cancel a scheduled task."""
        result = AsyncResult(celery_task_id, app=app)
        if result.state in ("PENDING", "RETRY"):
            result.revoke(terminate=True)
            logger.info(f"Cancelled Celery task {celery_task_id}")
            return True
        return False

    async def schedule_periodic_tasks(self):
        """
        Schedule all recurring tasks based on user preferences:
        - SEO analysis: monthly
        - CMS publishing: weekly
        - Crosslinking: weekly per article
        """
        users = await supabase_client.fetch_all("users", {"active": True})

        for user in users:
            user_id = user["id"]
            settings = await supabase_client.fetch_one("user_settings", {"user_id": user_id})
            prefs = settings.get("preferences", {}) if settings else {}

            # Schedule SEO analysis
            seo_params = get_schedule_params(prefs, "seo_analysis_frequency", "seo_analysis_datetime", 30*24*3600)
            await self.schedule_task("publish_seo_recs", args=[str(user_id)], **seo_params)

            # Schedule CMS publishing
            pending_jobs = await supabase_client.fetch_all("blog_results", {"user_id": user_id, "status": "pending"})
            cms_params = get_schedule_params(prefs, "cms_publish_frequency", "cms_publish_datetime", 7*24*3600)
            for job in pending_jobs:
                await self.schedule_task("cms_publishing", args=[job["id"]], **cms_params)

            # Schedule crosslinking
            articles = await supabase_client.fetch_all("blog_results", {"user_id": user_id, "status": "published"})
            crosslink_params = get_schedule_params(prefs, "crosslink_frequency", "crosslink_datetime", 7*24*3600)
            for article in articles:
                await self.schedule_task("crosslink_blogs", args=[article["id"]], **crosslink_params)

        logger.info(
            f"Scheduled periodic tasks for {len(users)} users"
        )



# ✅ Singleton instance
scheduler_service = SchedulerService()
