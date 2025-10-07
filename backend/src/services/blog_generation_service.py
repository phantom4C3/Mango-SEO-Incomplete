# backend\src\services\blog_generation_service.py
import logging 
from typing import Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from .task_service import TaskService  # ✅ Use unified service
from ..clients.supabase_client import supabase_client 
from ..core.config import settings
from ..services.realtime_listener_service import realtime_listener_service
import re
import httpx 
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_language(language_code: str) -> bool:
        return language_code.lower() in settings.languages_supported


def validate_and_normalize_url(url: str) -> str:
        if not url:
            raise HTTPException(status_code=400, detail="Website URL is required")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urlparse(url)
        if not parsed.netloc or not re.match(
            r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", parsed.netloc
        ):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        return url


async def scrape_website_basic(url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"User-Agent": "MangoSEO-Bot/1.0 (+https://mangoseo.com)"}
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                html_content = response.text
                title_match = re.search(
                    r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE
                )
                title = title_match.group(1).strip() if title_match else "No title found"
                desc_match = re.search(
                    r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
                    html_content,
                    re.IGNORECASE,
                )
                description = (
                    desc_match.group(1).strip() if desc_match else "No description found"
                )
                lang_match = re.search(
                    r'<html[^>]*lang=["\'](.*?)["\']', html_content, re.IGNORECASE
                )
                detected_language = (
                    lang_match.group(1).split("-")[0] if lang_match else "en"
                )
                return {
                    "url": url,
                    "title": title,
                    "description": description,
                    "detected_language": detected_language,
                    "status_code": response.status_code,
                    "content_length": len(html_content),
                    "final_url": str(response.url),
                }
        except httpx.RequestError as e:
            logger.error(f"Website scraping failed for {url}: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Failed to access website: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during scraping {url}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze website")
        
class BlogGenerationService:
    """Main orchestration service that coordinates all components for blog generation via ai blog generator microservice"""

    def __init__(self):
        self.realtime_listener = realtime_listener_service

    async def initialize(self):
        """Start the singleton listener asynchronously."""
        await self.realtime_listener.start_listening()
        logger.info("Realtime listener started for BlogGenerationService.")


    async def shutdown(self):
            # cleanup tasks
            await self.realtime_listener.stop_listening()
            # any other cleanup (e.g., closing DB clients)



    # ------------------- Article Generation ------------------- #
    async def start_article_generation(self, article_create, user_id: UUID):
        """Create an article generation task, call AI Worker, and save the generated content."""
        # Validate language
        if article_create.language not in settings.languages_supported:
            raise ValueError(
                f"Unsupported language '{article_create.language}'. "
                f"Supported: {', '.join(settings.languages_supported)}"
            )

        # 1️⃣ Create article in DB
        article = await supabase_client.create_article(article_create)

        # 2️⃣ Create a task in Supabase for tracking
        task = {
            "name": "article_generation",
            "user_id": str(user_id),
            "article_id": str(article.id),
            "status": "pending",
            "payload": article_create.dict(),
        }
        task_record = await supabase_client.insert_into("tasks", task)
        task_id = task_record[0]["id"] if task_record else str(uuid4())
        logger.info(
            f"Created article_generation task {task_id} for article {article.id}"
        )

        # 3️⃣ Call AI Worker generate API
        import httpx

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                payload = {
                    "task_type": "content_strategy",
                    "task_id": task_id,
                    "parameters": {
                        "website_url": article_create.website_url,
                        "topic": article_create.title,
                        "article_id": str(article.id),
                        "user_id": str(user_id),
                    },
                }
                headers = {"X-Internal-Secret": settings.ai_blog_writer_secret}


                response = await client.post(
                    f"{settings.ai_blog_writer_URL}/generate",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"AI Worker call failed for task {task_id}: {str(e)}")
            await supabase_client.update_table(
                "tasks",
                {"id": task_id},
                {
                    "status": "failed",
                    "updated_at": datetime.utcnow().isoformat(),
                    "result": {"error": str(e)},
                },
            )

        logger.info(
            f"Article generation initiated for task {task_id}, article {article.id}"
        )
        return task_id

    # ------------------- Website Onboarding Flow ------------------- #
    async def submit_website_onboarding(
        self, website_url: str, user_id: UUID, topic: str = "", style: str = ""
    ) -> str:
        """Create a website onboarding task. AI Worker handles scraping/SEO/optimization."""
        # ✅ Use unified task service
        task_id = await TaskService.create_task(
            user_id=user_id,
            task_type="blog_generation",
            payload={"topic": topic, "style": style},  # fixed
        )
        task_record = {
            "id": task_id,
            "name": "website_onboarding",
            "status": "pending",
            "payload": {"url": website_url, "user_id": str(user_id)},
            "result": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        try:
            await supabase_client.insert_into("tasks", task_record)
            logger.info(f"Created website_onboarding task {task_id} for {website_url}")
            return task_id
        except Exception as e:
            logger.error(
                f"Failed to create website_onboarding task for {website_url}: {str(e)}"
            )
            raise

    # ------------------- Save Results ------------------- #
    async def save_analysis_results(
        self, task_id: str, results: Dict[str, Any]
    ) -> None:
        """Save results to Supabase and mark task complete."""
        try:
            await supabase_client.update_table(
                "tasks",
                {"id": task_id},
                {
                    "status": "completed",
                    "result": results,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"Results saved for task {task_id}")
        except Exception as e:
            logger.error(f"Error saving analysis results for {task_id}: {str(e)}")
            raise


    async def cancel_pipeline(self, task_id: str) -> bool:
        """
        Cancel an ongoing content pipeline.
        Returns True if cancellation was successful.
        """
        try:
            # 1️⃣ Fetch the pipeline/task from Supabase
            task = await supabase_client.fetch_one("tasks", {"id": task_id})
            if not task:
                logger.warning(f"Pipeline {task_id} not found")
                return False

            status = task.get("status", "pending")

            # 2️⃣ Only cancel if pipeline is pending or running
            if status not in ["pending", "running"]:
                logger.info(f"Pipeline {task_id} cannot be cancelled (status={status})")
                return False

            # 3️⃣ Set cancellation flag in Supabase
            await supabase_client.update_table(
                "tasks",
                {"id": task_id},
                {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow().isoformat(),
                    "result": {"message": "Pipeline cancelled by user"},
                },
            )
            logger.info(f"Pipeline {task_id} marked as cancelled in Supabase")

            # 4️⃣ Stop any running agents/workers related to this pipeline
            if hasattr(self.realtime_listener, "stop_task"):
                await self.realtime_listener.stop_task(task_id)
                logger.info(f"Realtime listener stopped for pipeline {task_id}")

            return True

        except Exception as e:
            logger.error(f"Error cancelling pipeline {task_id}: {str(e)}")
            return False




blog_generation_service = BlogGenerationService()