import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class TaskService:
    """
    Static service for managing tasks and agent subtasks.
    Compatible with both pipeline-level retries and single-agent retries.
    """

    # -----------------------
    # Core Task Functions
    # ----------------------- 

    @staticmethod
    async def create_task(
        task_type: str,
        user_id: UUID,
        payload: Optional[Dict[str, Any]] = None,
        website_url: Optional[str] = None,
        agents: Optional[List[str]] = None,  # e.g., ["seo_analysis", "blog_generation"]
        website_id: Optional[UUID] = None
    ) -> str:
        """
        Creates a task in blog_tasks or seo_tasks, plus agent subtasks.
        """
        from ..services.scheduler_service import scheduler_service
        
        if payload is None:
            payload = {}
        if website_url:
            payload["website_url"] = website_url

        table_name = "blog_tasks" if task_type.startswith("blog") else "seo_tasks"

        task_data = {
            "user_id": str(user_id),
            "website_id": str(website_id) if website_id else None,
            "status": "pending",
            "progress_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Persist main task
        created = await supabase_client.insert_into(table_name, task_data)
        if not created:
            raise RuntimeError(f"Failed to create {table_name} task")

        task_id = created[0]["id"]

        # Optionally, schedule the task
        await scheduler_service.schedule_task(task_id, task_type, user_id, payload)

        logger.info(f"Created {table_name} task {task_id} with agents {agents or []}")
        return task_id


    @staticmethod
    async def list_tasks(user_id: Optional[UUID] = None, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if task_type:
            table_name = "blog_tasks" if task_type.startswith("blog") else "seo_tasks"
            filters = {"user_id": str(user_id)} if user_id else None
            return await supabase_client.fetch_all(table_name, filters)
        else:
            # Fetch from both tables
            filters = {"user_id": str(user_id)} if user_id else None
            blog_tasks = await supabase_client.fetch_all("blog_tasks", filters)
            seo_tasks = await supabase_client.fetch_all("seo_tasks", filters)
            return blog_tasks + seo_tasks

    @staticmethod
    async def retry_failed_task(task_id: UUID):
        from ..services.scheduler_service import scheduler_service
        
        task = await TaskService.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found for retry")
            return

        if task["status"] != "failed":
            logger.info(f"Task {task_id} is not failed (status={task['status']})")
            return

        task_type = task["task_type"]
        user_id = UUID(task["user_id"])
        payload = task.get("payload", {})

        logger.info(f"Retrying failed task {task_id} type={task_type}") 

        await TaskService.update_task_status(task_id, "retrying")

        # ✅ NEW: delegate retry to scheduler_service
        await scheduler_service.retry_task(task_id, task_type, user_id, payload)

    @staticmethod
    async def cancel_task(task_id: UUID):
        from ..services.scheduler_service import scheduler_service
        
        await TaskService.update_task_status(task_id, "cancelling")

        cancelled = await scheduler_service.cancel_scheduled_task(str(task_id))
        if cancelled:
            await TaskService.update_task_status(task_id, "cancelled")
        else:
            await TaskService.update_task_status(task_id, "cancellation_failed")

        # -----------------------
    # Agent Subtask Functions
    # -----------------------

    @staticmethod
    async def create_agent_subtask(
        parent_task_id: str,
        agent_type: str,
        parameters: Dict,
    ) -> str:
        """
        Creates a subtask record in seo_agent_runs or blog_agent_runs.
        """
        subtask_id = str(uuid.uuid4())

        agent_subtask = {
            "id": subtask_id,
            "task_id": parent_task_id,   # matches FK in blog/seo agent tables
            "agent_type": agent_type,
            "status": "pending",
            "attempt": 1,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
        }

        # ✅ Decide target table
        if agent_type.startswith("seo_"):
            table = "seo_agent_runs"
        elif agent_type.startswith("blog_"):
            table = "blog_agent_runs"
        else:
            raise RuntimeError(f"Unsupported agent_type: {agent_type}")

        try:
            await supabase_client.insert_into(table, agent_subtask)
        except Exception as e:
            logger.error(f"Failed to create {agent_type} subtask: {e}")
            raise

        return subtask_id


    @staticmethod
    async def retry_agent_subtask(task_id: str, agent_type: str) -> Dict[str, Any]:
        """
        Retry a single failed agent subtask for a given task.
        """
    
        from ..services.seo_workflow_service import seo_workflow_service
        from ..services.blog_generation_service import blog_generation_service

        if agent_type.startswith("seo_"):
            table = "seo_agent_runs"
        elif agent_type.startswith("blog_"):
            table = "blog_agent_runs"
        else:
            raise RuntimeError(f"Unsupported agent_type: {agent_type}")

        # 1. Find the failed subtask
        subtask = await supabase_client.fetch_one(
            table,
            {"task_id": str(task_id), "agent_type": agent_type, "status": "failed"}
        )

        if not subtask:
            raise RuntimeError(
                f"No failed subtask found for {agent_type} under task {task_id}"
            )

        # 2. Update → retrying
        await supabase_client.update_table(
            table,
            {"id": subtask["id"]},
            {
                "status": "retrying",
                "attempt": subtask.get("attempt", 1) + 1,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

        # 3. Dispatch the retry
        if agent_type.startswith("seo_"):

            success = await seo_workflow_service.retry_agent(
                subtask["agent_type"], subtask.get("parameters", {})
            )
        elif agent_type.startswith("blog_"):
            
            success = await blog_generation_service.retry_agent(
                subtask["agent_type"], subtask.get("parameters", {})
            )

        # 4. Update final state
        await supabase_client.update_table(
            table,
            {"id": subtask["id"]},
            {
                "status": "completed" if success else "failed",
                "updated_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat() if success else None,
            }
        )

        updated_subtask = await supabase_client.fetch_one(
            table,
            {"id": subtask["id"]}
        )

        return updated_subtask

    @staticmethod
    async def link_job(task_id: str, job_id: str):
        await supabase_client.update_table("blog_tasks", {"id": task_id}, {"publishing_job_id": job_id})

    @staticmethod
    async def get_task(task_id: UUID, task_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not task_type:
            # try SEO first, then blog
            task = await supabase_client.fetch_one("seo_tasks", {"id": str(task_id)})
            if task:
                return task
            task = await supabase_client.fetch_one("blog_tasks", {"id": str(task_id)})
            return task
        table_name = "blog_tasks" if task_type.startswith("blog") else "seo_tasks"
        return await supabase_client.fetch_one(table_name, {"id": str(task_id)})



task_service = TaskService()



# 1. Task IDs from TaskService vs Celery

# TaskService TaskID

# Generated in your backend (probably UUID).

# Represents a business-level task (e.g., “SEO Analysis for site X”).

# Stored in Supabase → frontend can query it.

# Celery TaskID

# Auto-generated by Celery when you .delay() or .apply_async().

# Represents a background job execution instance.

# Exists only inside Celery’s world (Redis/queue + worker).

# 👉 They are different IDs and serve different purposes.

# How to manage both?

# Always pass your own TaskService TaskID to microservices (SEO, Blog, CMS).

# If Celery is used internally, you can store Celery’s task_id as a metadata field in Supabase (e.g., celery_task_id). But the primary ID should always be the TaskService one — because it’s stable and frontend-friendly.