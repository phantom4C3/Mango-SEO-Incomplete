# backend/src/services/seo_workflow_service.py
import logging
from typing import List, Dict, Any
import httpx
from uuid import UUID
from datetime import datetime

from ..clients.supabase_client import supabase_client
from ..core.config import settings
from shared_models.models import SEOAnalysisStatus, TaskStatus
from ..core.auth import get_service_headers

logger = logging.getLogger(__name__)

class SEOWorkflowService:
    def __init__(self):
        self.onpageseo_base_url = settings.onpageseo_url

    # ---------- Public Methods ----------

   
    async def initiate_seo_analysis(self, task_id: str) -> str:
        """Trigger SEO analysis through OnPageSEO service for a single task"""
        from .task_service import TaskService  # move import here

        
        task_data = await TaskService.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task {task_id} not found")

        url = task_data.get("url")
        user_id = task_data.get("user_id")
        if not url or not user_id:
            raise ValueError(f"Task {task_id} missing URL or user_id")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "url": url,
                    "user_id": user_id,
                    "task_id": task_id,
                }
                headers = get_service_headers("onpageseo")
                response = await client.post(
                    f"{self.onpageseo_base_url}/api/v1/analyze",
                    json=payload,
                    headers=headers,
                    timeout=300
                )

                if response.status_code != 200:
                    error_msg = f"SEO analysis failed: {response.text}"
                    await TaskService.update_task_status(task_id, TaskStatus.FAILED, error_msg)
                    raise Exception(error_msg)

            await TaskService.update_task_status(task_id, TaskStatus.PROCESSING, "SEO analysis started")
            return task_id
        except Exception as e:
            error_msg = f"Failed to initiate SEO analysis: {str(e)}"
            await TaskService.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            raise

    async def get_analysis_status(self, task_id: str) -> SEOAnalysisStatus:
        """Get SEO analysis status and recommendations"""
        from .task_service import TaskService  # move import here

        try:
            task_data = await TaskService.get_task(task_id)
            if not task_data:
                raise ValueError(f"Task {task_id} not found")

            recommendations = []
            if task_data.status == TaskStatus.COMPLETED:
                # async-compatible fetch
                recommendations = await supabase_client.fetch_all(
                    "ai_recommendations", 
                    filters={"task_id": task_id}
                )

            return SEOAnalysisStatus(
                task_id=task_id,
                status=task_data.status,
                progress_message=task_data.progress_message or "",
                recommendations=recommendations,
                created_at=task_data.created_at,
                updated_at=task_data.updated_at,
                completed_at=task_data.completed_at
            )
        except Exception as e:
            logger.error(f"Failed to get analysis status: {str(e)}")
            raise

    async def process_batch_analysis(self, task_id: str) -> None:
        """Process batch URLs sequentially using TaskService"""
        from .task_service import TaskService  # move import here
        # Fetch URLs linked to this task
        task_data = await TaskService.get_task(task_id)
        if not task_data:
            await TaskService.update_task_status(task_id, TaskStatus.FAILED, "Task not found")
            return

        website_id = task_data.get("website_id")
        if not website_id:
            await TaskService.update_task_status(task_id, TaskStatus.FAILED, "Website ID missing")
            return

        urls = await supabase_client.fetch_all("urls", filters={"website_id": website_id})
        if not urls:
            await TaskService.update_task_status(task_id, TaskStatus.FAILED, "No URLs found for this website")
            return

        # Process batch sequentially
        for i, url_data in enumerate(urls):
            subtask_id = await TaskService.create_agent_subtask(
                parent_task_id=task_id,
                agent_type="seo_analysis",
                parameters={"url_id": url_data["id"]}
            )
            try:
                await self._process_single_analysis_item(subtask_id)
                await TaskService.update_task_status(subtask_id, TaskStatus.COMPLETED, "Item processed successfully")
            except Exception as e:
                await TaskService.update_task_status(subtask_id, TaskStatus.FAILED, str(e))

        await TaskService.update_task_status(task_id, TaskStatus.COMPLETED, "Batch processing completed")


    async def _get_recommendations_by_ids(self, task_id: str) -> List[Dict[str, Any]]:
        """Fetch recommendations by task_id for frontend display"""
        return await supabase_client.fetch_all("ai_recommendations", {"task_id": task_id})

    # ---------- Internal Methods ----------

    async def _process_batch(
        self,
        items: List[Any],
        process_single_fn: callable,
        task_id: str,
        website_id: str,
        progress_message_template: str
    ) -> List[Dict[str, Any]]:
        results = []
        total_items = len(items)
        from .task_service import TaskService  # move import here

        for i, item in enumerate(items):
            progress_msg = progress_message_template.format(
                current=i+1,
                total=total_items,
                item=item.get("url", f"item {i+1}")
            )
            await TaskService.update_task_status(task_id, TaskStatus.PROCESSING, progress_msg)

            try:
                subtask_id = await TaskService.create_subtask(
                    parent_task_id=task_id,
                    task_type="batch_analysis_item",
                    parameters={"item": item}
                )

                result = await process_single_fn(item, subtask_id)
                results.append({**result, "success": True})
                await TaskService.update_task_status(subtask_id, TaskStatus.COMPLETED, "Item processed successfully")

            except Exception as e:
                logger.error(f"Failed to process {item}: {str(e)}")
                results.append({"error": str(e), "success": False, "item": item})
                if "subtask_id" in locals():
                    await TaskService.update_task_status(subtask_id, TaskStatus.FAILED, f"Failed: {str(e)}")

        await self._store_batch_results(website_id, task_id, results)

        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        final_message = f"Batch completed: {successful} successful, {failed} failed"
        await TaskService.update_task_status(task_id, TaskStatus.COMPLETED, final_message)

        return results

    async def _process_single_analysis_item(self, url_data: dict, subtask_id: str) -> dict:
        """Process a single URL for analysis (no UUID fallback)"""
        await self.initiate_seo_analysis(
            url_data["url"],
            UUID(url_data["user_id"]),
            subtask_id,
            depth=1,
            analysis_type="comprehensive"
        )
        return {
            "url_id": url_data["id"],
            "url": url_data["url"],
            "task_id": subtask_id
        }

    async def _store_batch_results(self, website_id: str, task_id: str, results: List[Dict[str, Any]]):
        """Store batch results"""
        summary = {
            "total_pages": len(results),
            "successful_analyses": sum(1 for r in results if r.get("success", False)),
            "failed_analyses": sum(1 for r in results if not r.get("success", True)),
            "generated_at": datetime.utcnow().isoformat()
        }
        batch_data = {
            "website_id": website_id,
            "task_id": task_id,
            "results": results,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat()
        }
        await supabase_client.insert_into("batch_results", batch_data)

    async def _get_website_urls(self, website_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch website URLs from Supabase"""
        return await supabase_client.fetch_all(
            "urls",
            filters={"website_id": website_id},
            select="id,url,user_id",
            limit=limit
        )


seo_workflow_service = SEOWorkflowService()






#####################
# Batch analysis:

# Currently, process_batch_analysis loops through URLs and calls _process_single_analysis_item, which calls initiate_seo_analysis.

# That means batch requests are simulated by looping over single /analyze calls.

# You do not yet call /analyze/batch from seo_workflow_service.

# ✅ Supported by OnPageSEO service?

# /analyze ✅ Supported.

# /analyze/batch ✅ Exists, but not used by SEOWorkflowService currently.
# # Instead of looping over URLs:
# async with httpx.AsyncClient() as client:
#     payload = {"urls": list_of_urls, "task_ids": list_of_task_ids}
#     headers = get_service_headers("onpageseo")
#     response = await client.post(f"{self.onpageseo_base_url}/api/v1/analyze/batch",
#                                  json=payload,
#                                  headers=headers,
#                                  timeout=600)








# Conclusion

# Mostly compatible, but two key fixes required:

# Implement TaskService.create_subtask or replace _process_batch calls with create_agent_subtask.

# Fix the signature mismatch for initiate_seo_analysis vs _process_single_analysis_item.

# Once fixed, seo_workflow_service and pixel_service can safely operate in the same codebase and integrate with their respective endpoints.