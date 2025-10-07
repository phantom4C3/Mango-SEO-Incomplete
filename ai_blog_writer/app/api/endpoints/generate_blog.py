# ai_blog_writer\app\api\endpoints\generate_blog.py
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...core.security import verify_internal_secret
from ...clients.supabase_client import supabase_client
from ...core.content_pipeline import (
    content_pipeline,
)  # ✅ NEW: Import the new ContentPipeline

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


class GenerateRequest:
    """Request model for the new generate endpoint"""

    def __init__(
        self,
        task_id: str,
        topic: str,
        target_keyword: str,
        user_id: str,
        website_url: str = None,
        competitors: list = None,
        language: str = "en",
        tone: str = "professional",
    ):
        self.task_id = task_id
        self.topic = topic
        self.target_keyword = target_keyword
        self.user_id = user_id
        self.website_url = website_url
        self.competitors = competitors or []
        self.language = language
        self.tone = tone
        self.task_id = task_id


async def _run_content_pipeline_with_callback(
    task_id: str,
    topic: str,
    target_keyword: str,
    user_id: str,
    website_url: str = None,
    language: str = "en",
    tone: str = "professional",
    competitors: list = None,  # <-- add this
):
    competitors = competitors or []
    """
    Runs the content pipeline in the background.
    Handles the complete blog generation process from strategy to final review.
    """
    print(
        f"🔧 Starting content pipeline for {task_id}, topic: {topic}, keyword: {target_keyword}"
    )

    try:
        logger.info(
            f"Running content pipeline: {task_id} for topic: {topic}, keyword: {target_keyword}"
        )

        # Execute the complete pipeline
        result = await content_pipeline.execute_blog_creation(
            task_id=task_id,
            website_url=website_url,
            user_id=user_id,
            language=language,
            tone=tone,
            competitors=competitors
        )

        logger.info(f"Pipeline completed: {task_id} | Status: {result.get('status')}")

        print(
            f"✅ Pipeline finished for {task_id}, result status: {result.get('status')}"
        )

    except Exception as e:
        logger.exception(f"Pipeline failed for {task_id}: {str(e)}")
        # Error status is already updated by the pipeline itself


# ✅ enforce internal secret check
@router.post("/generate", status_code=202, dependencies=[Depends(verify_internal_secret)])
async def generate_blog(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    ✅ Generate complete blog content using the unified ContentPipeline.
    Access restricted via X-Internal-Secret header.
    """

    print("🔹 [API] /generate called with payload:", payload)

    try:
        required_fields = ["task_id", "topic", "user_id"]
        if not all(key in payload for key in required_fields):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {required_fields}. Got: {list(payload.keys())}",
            )

        task_id = payload["task_id"]
        topic = payload["topic"]
        user_id = payload["user_id"]
        website_url = payload.get("website_url")
        competitors = payload.get("competitors", [])
        language = payload.get("language", "en")
        tone = payload.get("tone", "professional")

        logger.info(f"Accepted blog generation task: {task_id} for topic: {topic}")

        await supabase_client.insert_into(
            "blog_results",
            {
                "task_id": task_id,
                "user_id": user_id,
                "title": topic,
                "final_content": "",
                "status": "pending",
                "language": language,
                "tone": tone,
                "created_at": datetime.now().isoformat(),
            },
        )

        background_tasks.add_task(
            _run_content_pipeline_with_callback,
            task_id=task_id,
            topic=topic,
            user_id=user_id,
            website_url=website_url,
            target_keyword=payload.get("target_keyword", ""),
            competitors=competitors,
            language=language,
            tone=tone,
        )

        return {
            "status": "accepted",
            "message": "Blog generation pipeline started",
            "task_id": task_id,
            "topic": topic,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to start blog generation pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

