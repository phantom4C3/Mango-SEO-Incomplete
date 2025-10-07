"""
Celery tasks for runtime execution of scheduled jobs.
Handles only the tasks that should be scheduled via Celery:
- CMS publishing
- Publishing SEO recommendations
- Relinking blogs after crosslinking
"""

import logging 
from uuid import UUID
from datetime import datetime
from uuid import uuid4
from celery import shared_task
from .clients.supabase_client import supabase_client
from .services.publish_cms_service import publish_cms_service
from .services.pixel_service import pixel_service
from .services.crosslinking_service import cross_linking_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def publish_to_cms_task(self, job_id: str):
    """
    Celery task that publishes an article via the dedicated CMS service.
    """
    try:
        # Fetch publishing job
        job = await supabase_client.fetch_one("blog_results", {"id": job_id})


        if not job:
            logger.error(f"No publishing job found for job_id={job_id}")
            return {"status": "error", "message": "Job not found"}

        article_id = job["id"]
        user_id = job["user_id"]

        # Publish article via CMS service
        result = await publish_cms_service.publish_article(UUID(article_id), UUID(user_id), task_id=job_id)

        # Update blog_results table as completed
        await supabase_client.update_table(
                "blog_results",
                {"id": job_id},
                {
                    "status": "completed",
                    "cms_publish_info": result,  # structured info from .CMS
                    "post_url": result.get("canonical_url"),  # optional single URL
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
        


        return {"status": "completed", "job_id": job_id, "result": result}

    except Exception as e:
        logger.error(f"Publishing failed: {str(e)}")

        # Update blog_results table as failed
        await supabase_client.update_table(
                "blog_results",
                {"id": job_id},
                {
                    "status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def publish_seo_recs_task(self, user_id: str):
    """
    Celery task that publishes SEO recommendations via the Pixel service.
    Ensures pixel_id is always passed and logs activity safely.
    """
    try:
        # Fetch recommendations
        recs = await supabase_client.fetch_all(
            "ai_recommendations",
            filters=[
                {"op": "eq", "col": "user_id", "val": user_id},
                {"op": "eq", "col": "user_approved", "val": True}
            ]
        )

        if not recs:
            logger.warning(f"No approved recommendations found for user_id={user_id}")
            return {"status": "no_recommendations", "user_id": user_id}

        # Build mapping: task_id → list of recommendation IDs
        task_map = {}
        for r in recs:
            pixel_id = r.get("pixel_id")
            if not pixel_id:
                continue
            task_id = r.get("task_id", "")
            task_map.setdefault(task_id, []).append(r["id"])

        # Deploy recommendations in batches per task_id
        for task_id, rec_ids in task_map.items():
            await pixel_service.deploy_recommendations(
                task_id=task_id,
                recommendation_ids=rec_ids,
                optimization_level="standard"
            )


                        

        # Use a unique ID per job for upsert
        job_id = str(uuid4())

        # Include all deployed recommendation IDs in the result
        rec_ids = [r["id"] for r in recs]

        await supabase_client.upsert(
            "seo_recommendation_jobs",
            {
                "id": job_id,
                "user_id": user_id,
                "recommendation_ids": rec_ids,
                "status": "completed",
                "result": {"published_count": len(recs)},
                "updated_at": datetime.utcnow().isoformat()
            }
        )


        return {"status": "completed", "user_id": user_id, "published_count": len(recs)}

    except Exception as e:
        logger.error(f"SEO recommendations publishing failed for user_id={user_id}: {e}")

        await supabase_client.upsert(
        "seo_recommendation_jobs",
        {
            "id": job_id,
            "user_id": user_id,
            "recommendation_ids": rec_ids,
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        }
    )

        raise self.retry(exc=e)

    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def crosslink_blogs_task(self, article_id: str):
    """
    Celery task that performs comprehensive relinking for a single blog article.
    """
    try:
        result = await cross_linking_service.relink_article(article_id)

        # Update log
        await supabase_client.upsert(
            "crosslink_jobs",
            {
                "id": article_id,
                "status": "completed",
                "result": result,
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        return {"status": "completed", "article_id": article_id, "result": result}

    except Exception as e:
        logger.error(f"Crosslinking task failed for {article_id}: {e}")

        await supabase_client.upsert(
                "crosslink_jobs",
                {
                    "id": article_id,
                    "status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

        raise self.retry(exc=e)







# Summary of the flow for each task
# publish_to_cms_task
# Celery schedules task → calls publish_cms_service.publish_article → updates Supabase status.
# publish_seo_recs_task
# Celery schedules task → calls pixel_service.publish_seo_recommendations → updates status.
# crosslink_blogs_task
# Celery schedules task → calls crosslink_service.relink_blogs → updates status.
# Services contain the actual work. Celery only handles asynchronous execution and retry logic.
# No other files are duplicating this execution logic.


# 3. Where exactly to call tasks.py methods?

# publish_to_cms_task
# 👉 Called from .scheduler_service.py (when a blog publish job is scheduled).

# crosslink_blogs_task
# 👉 Called from .publish_cms_service.py (right after publish success).

# crosslink_relinking_weekly (new)
# 👉 Called from .scheduler_service.py or directly by Celery Beat for weekly runs.

# publish_seo_recs_task
# 👉 Called from .either an endpoint (on-demand SEO push) or from .scheduler (if automated).








# | `tasks.py`             | SEO recommendations deployed one by one                                   | ⚠ Partially resolved. You’re batching recommendations by `task_id`, which improves efficiency, but within each `task_id` you call `deploy_recommendations` once per batch. If batch is very large, it’s still sequential. Could improve by parallelizing within batches if supported by `pixel_service`.         |
# | `scheduler_service.py` | Async `schedule_task` wrapping sync `apply_async`                         | ✅ This is acceptable. Using `async def` in scheduler is fine for awaiting DB calls; calling `apply_async` is naturally sync. No misleading `asyncio.run` used.                                                                                                                                                   |
# | `scheduler_service.py` | Potential duplicate scheduling                                            | ⚠ Not addressed here. `schedule_periodic_tasks` still fetches all pending/published jobs without checking if a Celery task for the same job is already scheduled. Could result in duplicates.                                                                                                                    |
# | `celery_app.py`        | `include` path must match                                                 | ✅ Assuming your folder structure is `backend/src/tasks.py`, `include=["backend.src.tasks"]` matches correctly. Tasks should register properly.                                                                                                                                                                   |
