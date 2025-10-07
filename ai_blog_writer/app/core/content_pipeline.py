# ai_blog_generator/app/pipelines/content_pipeline.py
import asyncio
import logging
import uuid
from typing import Dict, Any
from datetime import datetime
import inspect

from ..agents.topic_agent import TopicAgent
from ..agents.strategy_agent import StrategyAgent
from ..agents.writing_agent import BlogWritingAgent
from ..agents.review_agent import ReviewAgent
from ..agents.media_agent import MediaAgent
from ..agents.faq_agent import FAQAgent
from ..clients.supabase_client import supabase_client
from shared_models.models import UserSettings

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Orchestrates AI Blog Generator agents - handles complete content creation pipeline
    """

    def __init__(self):
        self.topic_agent = TopicAgent()
        self.strategy_agent = StrategyAgent()
        self.writing_agent = BlogWritingAgent()
        self.media_agent = MediaAgent()
        self.faq_agent = FAQAgent()
        self.review_agent = ReviewAgent()

        # Pipeline configuration
        self.default_timeout = 300  # 5 minutes timeout per agent
        self.max_retries = 2

    async def execute_blog_creation(
        self,
        task_id: str,
        website_url: str,
        user_id: str,
        language: str = "en",
        tone: str = "professional",
        competitors: list = None,  # ✅ define as None by default
    ) -> Dict[str, Any]:
        """
        Execute complete blog creation pipeline with proper task tracking.
        Expects topic(s) to already exist in DB from suggest_blog_topics step.
        """
        print(
            f"\n🚀 [Pipeline] Starting blog pipeline | task_id={task_id} user_id={user_id}"
        )
        pipeline_start = datetime.now()

        # 1. Fetch user settings
        user_settings_db = await supabase_client.fetch_one(
            "user_settings", filters={"user_id": user_id}
        )

        db_prefs = user_settings_db.get("preferences") if user_settings_db else {}

        # Ensure nested dicts exist for safe merge
        user_settings = {
            "user_id": user_id,
            "website_configs": db_prefs.get("website_configs", {}),
            "dashboard_preferences": db_prefs.get("dashboard_preferences", {}),
            "export_preferences": db_prefs.get("export_preferences", {}),
            **{
                k: v
                for k, v in db_prefs.items()
                if k
                not in [
                    "website_configs",
                    "dashboard_preferences",
                    "export_preferences",
                ]
            },
        }

        user_prefs = UserSettings(**user_settings)

        print(f"✅ User settings fetched: {bool(user_settings)}")

        try:
            # 2. Fetch existing topics
            print("📥 Fetching topics from DB...")
            topics = (
                await supabase_client.fetch_all("topics", filters={"task_id": task_id})
                or []
            )
            print(f"✅ Found {len(topics)} topics for this task")

            if not topics:
                raise ValueError(
                    "No topics found for this task. Please run topic suggestion first."
                )

            # 2a. Select topic
            topic = next((t for t in topics if t.get("is_selected")), topics[0])
            print(
                f"🎯 Selected topic: {topic['title']} | keyword={topic['target_keyword']}"
            )

            # 3. Strategy
            print("🛠 Generating content strategy...")
            content_strategy = await self._run_with_retry(
                self.strategy_agent.generate_content_strategy,
                topic=topic["title"],
                target_keyword=topic["target_keyword"],
                language=language,
                task_id=task_id,
                url_id=topic.get("url_id"),  # must exist and not None
            )
            print(
                f"✅ Strategy generated with {len(content_strategy.get('semantic_keywords', []))} semantic keywords"
            )

            # 4. Blog writing
            print("✍️ Writing blog draft...")
            blog_draft = await self._run_with_retry(
                self.writing_agent.generate_blog_draft,
                content_strategy=content_strategy,
                tone=tone,
                task_id=task_id,
                url_id=topic.get("url_id"),  # ✅ pass here
            )
            print(f"✅ Blog draft generated: {len(blog_draft.get('content',''))} chars")

            if not blog_draft or not blog_draft.get("content"):
                raise ValueError("Blog writing failed")

            # 4a. FAQs
            print("❓ Generating FAQs...")
            faqs = await self._run_with_retry(
                self.faq_agent.generate_faqs,
                blog_content=blog_draft["content"],
                target_keywords=content_strategy.get("semantic_keywords", []),
                language=language,
                task_id=task_id,
            )
            print(f"✅ FAQs generated: {len(faqs)}")

            # 5. Media
            headings = [
                sec.get("heading")
                for sec in blog_draft.get("sections", [])
                if sec.get("heading")
            ]
            print(f"🖼 Generating media assets for {len(headings)} headings...")
            media_assets = await self._run_with_retry(
                self.media_agent.generate_media_assets,
                headings=headings,
                title=blog_draft["title"],
                target_keyword=content_strategy["target_keyword"],
                website_url=website_url,
                user_prefs=user_prefs,  # ✅ Use the validated user_prefs here
                language=language,
                task_id=task_id,
            )
            print(f"✅ Media assets generated: {len(media_assets)}")

            # 6. Review
            print("🔍 Reviewing content quality...")
            review_results = await self._run_with_retry(
                self.review_agent.review_blog_content,
                blog_draft=blog_draft,
                content_strategy=content_strategy,
                task_id=task_id,
            )

            print(
                f"✅ Review completed | Score={review_results.get('overall_score', 0)}"
            )

            # 7. Compile results
            pipeline_end = datetime.now()
            execution_time = (pipeline_end - pipeline_start).total_seconds()
            print(f"📦 Compiling final result (took {execution_time:.2f}s)")

            final_result = {
                "task_id": task_id,
                "user_id": user_id,
                "website_url": website_url,                # string URL
                "website_id": user_prefs.website_configs.get(website_url, {}).get("id"),  # UUID
                "final_content": blog_draft["content"],
                "title": blog_draft["title"],
                "meta_description": blog_draft.get("meta_description", ""),
                "media_assets": media_assets,
                "quality_score": review_results.get("overall_score", 0),
                "topics": [topic],
                "content_strategy": content_strategy,
                "faqs": faqs,
                "execution_time": execution_time,
                "language": language,
                "tone": tone,
                "created_at": datetime.now().isoformat(),
                "status": "completed",
            }

            # 8. Save
            print("💾 Saving final results to DB...")
            await self._save_final_result(final_result)
            print("✅ Pipeline finished successfully!")

            return final_result

        except Exception as e:
            pipeline_end = datetime.now()
            execution_time = (pipeline_end - pipeline_start).total_seconds()
            print(f"❌ Pipeline failed after {execution_time:.2f}s: {str(e)}")
            raise

    async def _run_with_retry(self, agent_method, **kwargs):
        """
        Run an agent method with retry logic, backoff, and attempt logging.
        Only passes `url_id` to agents that accept it, maintaining backward compatibility.
        """
        max_attempts = self.max_retries
        result = None

        task_id = kwargs.get("task_id")
        # Use provided url_id if exists; otherwise, generate a temporary one
        url_id = kwargs.get("url_id") or str(uuid.uuid4())

        # Inspect agent method signature
        sig = inspect.signature(agent_method)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

        # Add url_id only if agent method accepts it
        if "url_id" in sig.parameters:
            filtered_kwargs["url_id"] = url_id

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"[Task {task_id}] Running {agent_method.__name__} attempt {attempt}"
                )

                # Run the agent method with timeout
                result = await asyncio.wait_for(
                    agent_method(**filtered_kwargs), timeout=self.default_timeout
                )

                # Log success in Supabase
                await supabase_client.insert_into(
                    "blog_agent_runs",
                    {
                        "task_id": task_id,
                        "url_id": url_id,
                        "agent_type": agent_method.__name__,
                        "attempt": attempt,
                        "status": "success",
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )

                logger.info(
                    f"[Task {task_id}] {agent_method.__name__} succeeded on attempt {attempt}"
                )
                return result

            except asyncio.TimeoutError:
                error_msg = f"Timeout on attempt {attempt}"
                logger.warning(f"[Task {task_id}] {agent_method.__name__} {error_msg}")

                await supabase_client.insert_into(
                    "blog_agent_runs",
                    {
                        "task_id": task_id,
                        "url_id": url_id,
                        "agent_type": agent_method.__name__,
                        "attempt": attempt,
                        "status": "timeout",
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"[Task {task_id}] {agent_method.__name__} attempt {attempt} failed: {error_msg}"
                )

                await supabase_client.insert_into(
                    "blog_agent_runs",
                    {
                        "task_id": task_id,
                        "url_id": url_id,
                        "agent_type": agent_method.__name__,
                        "attempt": attempt,
                        "status": "failed",
                        "error_message": error_msg,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )

            # Retry with exponential backoff if not last attempt
            if attempt < max_attempts:
                await asyncio.sleep(2 ** (attempt - 1))

        logger.error(
            f"[Task {task_id}] {agent_method.__name__} failed after {max_attempts} attempts"
        )
        raise RuntimeError(
            f"{agent_method.__name__} failed after {max_attempts} attempts"
        )

    async def _save_final_result(self, result: Dict[str, Any]):
        """Save final result to database - ORCHESTRATOR responsibility"""
        # Save to blog_results table
        blog_result = {
            "task_id": result["task_id"],
            "user_id": result["user_id"],
            "website_url": result["website_url"],
            "website_id": result["website_id"],
            "final_content": result["final_content"],
            "title": result["title"],
            "meta_description": result.get("meta_description", ""),
            "media_assets": result.get("media_assets", []),
            "quality_score": result.get("quality_score", 0),
            "content_strategy": result.get("content_strategy", {}),
            "faqs": result.get("faqs", []),  # <-- add this line
            "execution_time": result.get("execution_time", 0),
            "language": result.get("language", "en"),
            "tone": result.get("tone", "professional"),
            "created_at": result.get("created_at"),
            "status": result.get("status", "completed"),
            # Store only the selected topic reference (not full regenerated list)
            "topic_id": (
                result["topics"][0].get("id") if result.get("topics") else None
            ),
        }

        await supabase_client.insert_into("blog_results", blog_result)

        # 2️⃣ Update blog_tasks status
        await supabase_client.update_table(
            "blog_tasks",
            filters={"id": result["task_id"]},
            updates={
                "status": "completed",
                "updated_at": datetime.utcnow().isoformat(),
            },
        )

    async def execute_quick_mode(
        self,
        website_url: str,
        title: str,
        description: str,
        user_id: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Quick mode execution with simplified output
        """
        task_id = str(uuid.uuid4())

        result = await self.execute_blog_creation(
            task_id=task_id,
            website_url=website_url,
            title=title,
            description=description,
            user_id=user_id,
            language=language,
        )

        if result["status"] == "completed":
            return {
                "status": "success",
                "task_id": task_id,
                "title": result["title"],
                "content": result["final_content"],
                "quality_score": result["quality_score"],
                "execution_time": result["execution_time"],
            }
        else:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": result.get("error", "Unknown error"),
            }


# Singleton instance
content_pipeline = ContentPipeline()
